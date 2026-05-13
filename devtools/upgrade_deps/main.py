"""Upgrade dependencies in PEP 621/735 pyproject.toml + package.json manifests
to the latest stable from PyPI / npm.

Manifestos cubiertos:
    - server/pyproject.toml      (project.dependencies + dependency-groups)
    - devtools/pyproject.toml    (project.dependencies + dependency-groups)
    - dashboard/package.json
    - landing/package.json

Comportamiento:
    1. Parsea cada manifest en su esquema nativo (PEP 621/735 TOML o package.json).
    2. Consulta concurrentemente PyPI (https://pypi.org/pypi/<pkg>/json) o
       npm registry (https://registry.npmjs.org/<pkg>) por cada paquete.
    3. Filtra pre-releases (alpha/beta/rc/dev) y elige la version estable
       mas alta.
    4. Si la nueva version es mayor que la actual, reescribe el manifest
       conservando el prefijo original (==, ^, ~, >=, etc.) y el formato.

Flags:
    --dry-run   No escribe los manifestos; solo muestra que cambiaria.

Tras correr el script, regenerar lockfiles para que `uv sync --frozen` funcione:
    uv lock --project server
    uv lock --project devtools
"""

import asyncio
from pathlib import Path
import re

import httpx

from upgrade_deps.parsers import parse_package_json
from upgrade_deps.parsers import parse_pyproject_toml
from upgrade_deps.registry import fetch_npm_versions
from upgrade_deps.registry import fetch_pypi_versions
from upgrade_deps.reporter import ACTION_ERROR
from upgrade_deps.reporter import ACTION_OK
from upgrade_deps.reporter import ACTION_SKIP
from upgrade_deps.reporter import ACTION_UP
from upgrade_deps.reporter import print_summary
from upgrade_deps.reporter import print_table
from upgrade_deps.versions import format_with_prefix
from upgrade_deps.versions import is_newer
from upgrade_deps.versions import pick_latest_stable


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PYPI_MANIFESTS = (
    PROJECT_ROOT / 'server' / 'pyproject.toml',
    PROJECT_ROOT / 'devtools' / 'pyproject.toml',
)

NPM_MANIFESTS = (
    PROJECT_ROOT / 'dashboard' / 'package.json',
    PROJECT_ROOT / 'landing' / 'package.json',
)

# Concurrencia: limita a N requests simultáneos al mismo registry para no
# saturar PyPI/npm si un manifest es grande.
_CONCURRENCY = 10


async def _resolve_pypi_packages(
    client: httpx.AsyncClient,
    packages: list[dict],
) -> list[dict]:
    """Para cada paquete PyPI: fetch versions y decide si upgrade."""
    sem = asyncio.Semaphore(_CONCURRENCY)

    async def resolve(pkg: dict) -> dict:
        async with sem:
            try:
                versions = await fetch_pypi_versions(client, pkg['name'])
            except Exception as exc:  # noqa: BLE001
                return {
                    **pkg,
                    'current': pkg['version'],
                    'latest': None,
                    'action': ACTION_ERROR,
                    'reason': str(exc),
                }

        return _decide_pypi(pkg, versions)

    return await asyncio.gather(*(resolve(p) for p in packages))


def _decide_pypi(pkg: dict, versions: list[str]) -> dict:
    if not versions:
        return {
            **pkg,
            'current': pkg['version'],
            'latest': None,
            'action': ACTION_ERROR,
            'reason': 'no version found',
        }

    latest = pick_latest_stable(versions)
    if latest is None:
        return {
            **pkg,
            'current': pkg['version'],
            'latest': None,
            'action': ACTION_SKIP,
            'reason': 'only prereleases',
        }

    if is_newer(current=pkg['version'], candidate=latest):
        action = ACTION_UP
    else:
        action = ACTION_OK

    return {
        **pkg,
        'current': pkg['version'],
        'latest': latest,
        'action': action,
    }


async def _resolve_npm_packages(
    client: httpx.AsyncClient,
    packages: list[dict],
) -> list[dict]:
    sem = asyncio.Semaphore(_CONCURRENCY)

    async def resolve(pkg: dict) -> dict:
        async with sem:
            try:
                versions = await fetch_npm_versions(client, pkg['name'])
            except Exception as exc:  # noqa: BLE001
                return {
                    **pkg,
                    'current': pkg['version'],
                    'latest': None,
                    'action': ACTION_ERROR,
                    'reason': str(exc),
                }

        return _decide_npm(pkg, versions)

    return await asyncio.gather(*(resolve(p) for p in packages))


def _decide_npm(pkg: dict, versions: list[str]) -> dict:
    if not versions:
        return {
            **pkg,
            'current': pkg['version'],
            'latest': None,
            'action': ACTION_ERROR,
            'reason': 'no version found',
        }

    latest = pick_latest_stable(versions)
    if latest is None:
        return {
            **pkg,
            'current': pkg['version'],
            'latest': None,
            'action': ACTION_SKIP,
            'reason': 'only prereleases',
        }

    if is_newer(current=pkg['version'], candidate=latest):
        action = ACTION_UP
    else:
        action = ACTION_OK

    return {
        **pkg,
        'current': pkg['version'],
        'latest': latest,
        'action': action,
    }


def _write_pyproject_toml(path: Path, results: list[dict]) -> int:
    """Reescribe pyproject.toml aplicando upgrades. Preserva formato.

    Sustituye la spec original (`pkg['original']`, e.g. `"Django==6.0.4"`)
    por la nueva (`Django==6.0.5`) en la linea exacta donde aparecia. Si el
    parser no encontro la linea (`line_no == 0`), se omite — escenario raro
    (e.g. spec en multiples lineas) que no soportamos para no corromper formato.

    Retorna número de cambios escritos.
    """
    upgrades = [r for r in results if r['action'] == ACTION_UP]
    if not upgrades:
        return 0

    lines = path.read_text().splitlines(keepends=True)

    # Agrupamos upgrades por line_no para soportar (en teoria) multiples deps
    # en la misma linea, aunque pyproject.toml usualmente tiene una por linea.
    by_line: dict[int, list[dict]] = {}
    for pkg in upgrades:
        if pkg.get('line_no', 0) > 0:
            by_line.setdefault(pkg['line_no'], []).append(pkg)

    applied = 0
    new_lines: list[str] = []
    for idx, raw in enumerate(lines, start=1):
        pkgs = by_line.get(idx)
        if not pkgs:
            new_lines.append(raw)
            continue

        modified = raw
        for pkg in pkgs:
            old_spec = pkg['original']
            new_spec = (
                f'{pkg["name"]}{pkg["extras"]}{pkg["operator"]}{pkg["latest"]}'
            )
            # Replace inside the quoted string only (handles both quote styles).
            for quote in ('"', "'"):
                target = f'{quote}{old_spec}{quote}'
                replacement = f'{quote}{new_spec}{quote}'
                if target in modified:
                    modified = modified.replace(target, replacement, 1)
                    applied += 1
                    break

        new_lines.append(modified)

    path.write_text(''.join(new_lines))
    return applied


# Replace inside package.json preservando indent/quoting con regex linea-a-linea.
# Es mas seguro que re-serializar JSON (perderiamos el formato exacto del file).
def _replace_package_json_version(
    text: str,
    name: str,
    new_spec: str,
) -> tuple[str, bool]:
    """Reemplaza ``"name": "..."`` por ``"name": "<new_spec>"`` en text."""
    # Match: indent + "name" + : + ws + "spec" + opcional coma
    pattern = re.compile(
        r'(?P<head>"' + re.escape(name) + r'"\s*:\s*")'
        r'(?P<spec>[^"]*)'
        r'(?P<tail>")',
    )
    new_text, count = pattern.subn(
        lambda m: f'{m.group("head")}{new_spec}{m.group("tail")}',
        text,
        count=1,  # Solo el primer match (evita colisiones improbables)
    )
    return new_text, count > 0


def _write_package_json(path: Path, results: list[dict]) -> int:
    """Reescribe package.json aplicando upgrades. Retorna # cambios."""
    upgrades = [r for r in results if r['action'] == ACTION_UP]
    if not upgrades:
        return 0

    text = path.read_text()
    applied = 0

    for pkg in upgrades:
        new_spec = format_with_prefix(
            prefix=pkg['prefix'],
            version=pkg['latest'],
        )
        text, ok = _replace_package_json_version(text, pkg['name'], new_spec)
        if ok:
            applied += 1

    path.write_text(text)
    return applied


def _aggregate_stats(all_results: list[dict]) -> dict:
    return {
        'upgraded': sum(1 for r in all_results if r['action'] == ACTION_UP),
        'ok': sum(1 for r in all_results if r['action'] == ACTION_OK),
        'skip': sum(1 for r in all_results if r['action'] == ACTION_SKIP),
        'error': sum(1 for r in all_results if r['action'] == ACTION_ERROR),
    }


async def _process_pypi_manifest(
    client: httpx.AsyncClient,
    manifest: Path,
    dry_run: bool,
) -> tuple[list[dict], int]:
    rel_path = manifest.relative_to(PROJECT_ROOT).as_posix()
    packages = parse_pyproject_toml(manifest)
    if not packages:
        return [], 0

    results = await _resolve_pypi_packages(client, packages)
    print_table(
        [
            {
                'name': r['name'],
                'current': r['current'],
                'latest': r['latest'],
                'action': r['action'],
            }
            for r in results
        ],
        manifest=rel_path,
    )

    written = 0 if dry_run else _write_pyproject_toml(manifest, results)
    return results, written


async def _process_npm_manifest(
    client: httpx.AsyncClient,
    manifest: Path,
    dry_run: bool,
) -> tuple[list[dict], int]:
    rel_path = manifest.relative_to(PROJECT_ROOT).as_posix()
    packages = parse_package_json(manifest)
    if not packages:
        return [], 0

    results = await _resolve_npm_packages(client, packages)
    print_table(
        [
            {
                'name': r['name'],
                'current': r['current'],
                'latest': r['latest'],
                'action': r['action'],
            }
            for r in results
        ],
        manifest=rel_path,
    )

    written = 0 if dry_run else _write_package_json(manifest, results)
    return results, written


async def _run(*, dry_run: bool) -> int:
    print()
    print('=' * 60)
    if dry_run:
        print('  upgrade_deps [DRY-RUN]')
    else:
        print('  upgrade_deps')
    print('=' * 60)

    all_results: list[dict] = []
    total_written = 0

    async with httpx.AsyncClient() as client:
        for manifest in PYPI_MANIFESTS:
            results, written = await _process_pypi_manifest(
                client,
                manifest,
                dry_run,
            )
            all_results.extend(results)
            total_written += written

        for manifest in NPM_MANIFESTS:
            results, written = await _process_npm_manifest(
                client,
                manifest,
                dry_run,
            )
            all_results.extend(results)
            total_written += written

    stats = _aggregate_stats(all_results)
    print_summary(stats)

    if dry_run:
        print(f'  (dry-run: {stats["upgraded"]} cambios SIN aplicar)')
    else:
        print(f'  Manifestos actualizados: {total_written} cambios escritos')
    print()

    return 1 if stats['error'] else 0


def main(flags: dict) -> int:
    """Entry point invoked by ``devtools/run.py``."""
    return asyncio.run(_run(dry_run=flags.get('dry_run', False)))
