"""Lint and format commands (Ruff for server/devtools, Biome for dashboard/landing).

The ``test`` command was removed in Fase 3 of the CLI refactor — use
``python devtools/run.py test_runner`` for the unified test orchestrator
instead. The shim that returns a migration message lives in ``main.py``.
"""

from __future__ import annotations

import json
from typing import Any

from shared.compose import compose_exec
from shared.compose import ensure_running
from shared.console import _err
from shared.console import _header
from shared.console import _ok
from shared.console import _step
from shared.console import _warn
from shared.test_executors import _print_captured_output
from shared.test_executors import check_no_js_files


_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')

# Portfolio frontend modules:
#   - 6 Astro apps (each runs Biome via `pnpm exec biome check`)
#   - 5 shared packages (idem)
# Module names: app name directo ('hub', 'generic', ...) y 'pkg-<name>' para packages.
FRONTEND_MODULES = tuple(_PORTFOLIO_APPS) + tuple(
    f'pkg-{p}' for p in _PORTFOLIO_PACKAGES
)
PYTHON_MODULES = ('server', 'devtools')

# Módulos Python: cada uno tiene su ruff.toml autocontenido en su raíz.
# Ruff autodetecta el config cuando el cwd es la raíz del módulo.
_PYTHON_MODULE_META: dict[str, dict[str, str]] = {
    'server': {'workdir': '/app/server', 'strip_prefix': 'server/'},
    'devtools': {'workdir': '/app/devtools', 'strip_prefix': 'devtools/'},
}


def _parse_files_flag(
    flags: dict[str, Any], module: str = 'server'
) -> list[str]:
    """Extract the file list from --files flag (Python modules only).

    Files come as paths relative to project root (e.g. server/apps/foo.py).
    Strips the module prefix so the paths align with Docker workdir
    (``/app/<module>``). Returns ``['.']`` for "all files" when --files
    is empty.
    """
    files_raw = flags.get('files', '')
    if not files_raw:
        return ['.']

    strip_prefix = _PYTHON_MODULE_META.get(module, {}).get('strip_prefix', '')
    files = []
    for f in files_raw.replace(';', ' ').split():
        f = f.strip()
        if not f:
            continue
        if strip_prefix:
            f = f.removeprefix(strip_prefix)
        files.append(f)

    return files or ['.']


def _biome_command(pkg_script: str) -> list[str]:
    """Convierte el nombre de script (lint, lint:fix, format) a cmd Biome real.

    Portfolio NO tiene scripts `lint`/`format` por app. Biome corre desde
    el root del monorepo (la config `biome.json` esta en raíz). Por eso
    invocamos directamente `npx @biomejs/biome` con el cwd del módulo.
    """
    if pkg_script == 'lint':
        return ['npx', '@biomejs/biome', 'check', '.']
    if pkg_script == 'lint:fix':
        return ['npx', '@biomejs/biome', 'check', '--write', '.']
    if pkg_script == 'format':
        return ['npx', '@biomejs/biome', 'format', '--write', '.']
    # Fallback: si llega otro script, dejamos que pnpm intente resolverlo.
    return ['pnpm', 'run', pkg_script]


def _run_frontend_conformance(
    env: str,
    *,
    module: str,
    pkg_script: str,
    quiet: bool = False,
) -> int:
    """Run Biome dentro del container de la app o package del portfolio.

    Resuelve workdir desde docker._helpers para apps Astro (`/app/apps/<X>`)
    y packages (`/app/packages/<X>`). Si el module no tiene container
    dedicado, cae al `generic` para tener acceso a node_modules.
    """
    js_files = check_no_js_files(module)
    if js_files:
        _err(
            f'{module}/ contiene {len(js_files)} archivo(s) .js (solo .ts permitido):',
        )
        for f in js_files:
            print(f'  - {f}')
        return 1

    cmd = _biome_command(pkg_script)

    # Para packages (pkg-<X>) o apps con container propio: ejecutar en su
    # workdir. Si es package, no hay container con ese nombre, usamos
    # `generic` (cualquiera) y override workdir.
    target_service = module
    target_workdir = None
    if module.startswith('pkg-'):
        pkg = module.removeprefix('pkg-')
        target_service = 'generic'  # container generico para tener node_modules
        target_workdir = f'/app/packages/{pkg}'

    result = compose_exec(
        env,
        target_service,
        cmd,
        timeout=60,
        capture=quiet,
        workdir=target_workdir,
    )

    if result.returncode != 0:
        if quiet:
            _print_captured_output(result)
        return 1

    return 0


def _ruff_workdir(module: str) -> str:
    """Return Docker workdir for a Python module's ruff invocation."""
    return _PYTHON_MODULE_META[module]['workdir']


def _run_ruff_on_host(
    targets: list[str],
    *,
    workdir_relative: str,
    output_format: str = 'console',
) -> int:
    """Run Ruff directly on host (uses devtools/.venv/bin/ruff).

    Portfolio no tiene container Django; los módulos Python (devtools,
    server stub) corren ruff localmente via el venv ya sincronizado.
    """
    from pathlib import Path
    import subprocess

    from shared.paths import PROJECT_ROOT

    ruff_bin = PROJECT_ROOT / 'devtools' / '.venv' / 'bin' / 'ruff'
    if not ruff_bin.exists():
        _err(f'No se encontro ruff en {ruff_bin}')
        return 1

    cwd = PROJECT_ROOT / workdir_relative if workdir_relative else PROJECT_ROOT
    cmd = [str(ruff_bin), 'check', *targets]
    if output_format == 'json':
        cmd.extend(['--output-format', 'json', '--no-fix'])

    result = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
    return result.returncode


def cmd_lint(flags: dict[str, Any]) -> int:
    """Run linter (Ruff for server/devtools, Biome for portfolio apps/packages)."""
    env = flags['env']
    module = flags.get('module', 'server')

    if module in FRONTEND_MODULES:
        _header(f'biome check [{env}] {module}')
        if not ensure_running(env):
            return 1
        _step(f'Ejecutando Biome check en {module} (lint + format)...')
        rc = _run_frontend_conformance(env, module=module, pkg_script='lint')
        if rc != 0:
            _err('Biome encontro problemas')
            return 1
        _ok('Biome check limpio')
        return 0

    # Python: ejecutar ruff en host (no hay container server en portfolio).
    targets = _parse_files_flag(flags, module=module)
    output_format = flags.get('output_format', 'console')
    _header(f'ruff lint [host] {module}')
    _step('Ejecutando Ruff lint en host (devtools/.venv)...')

    workdir_rel = module if module != 'server' else 'server'
    rc = _run_ruff_on_host(
        targets,
        workdir_relative=workdir_rel,
        output_format=output_format,
    )
    if rc != 0:
        _err('Lint encontro problemas')
        return rc

    _ok('Lint limpio')
    return 0


def cmd_lint_fix(flags: dict[str, Any]) -> int:
    """Run linter with auto-fix (Ruff for server/devtools, Biome for dashboard/landing)."""
    env = flags['env']
    module = flags.get('module', 'server')

    if module in FRONTEND_MODULES:
        _header(f'biome check --fix [{env}] {module}')
        if not ensure_running(env):
            return 1
        _step(f'Ejecutando Biome check en {module} con auto-fix...')
        rc = _run_frontend_conformance(
            env,
            module=module,
            pkg_script='lint:fix',
        )
        if rc != 0:
            _warn('Algunos problemas no pudieron auto-corregirse')
            return 1
        _ok('Biome fix completado')
        return 0

    # Python: ruff fix en host.
    from pathlib import Path
    import subprocess

    from shared.paths import PROJECT_ROOT

    targets = _parse_files_flag(flags, module=module)
    _header(f'ruff lint --fix [host] {module}')

    ruff_bin = PROJECT_ROOT / 'devtools' / '.venv' / 'bin' / 'ruff'
    if not ruff_bin.exists():
        _err(f'No se encontro ruff en {ruff_bin}')
        return 1

    cwd = PROJECT_ROOT / module
    cmd = [str(ruff_bin), 'check', *targets, '--fix']
    _step('Ejecutando Ruff lint con auto-fix (host)...')
    result = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
    if result.returncode != 0:
        _warn('Algunos problemas no pudieron auto-corregirse')
        return 1
    _ok('Lint fix completado')
    return 0


def cmd_format(flags: dict[str, Any]) -> int:
    """Run formatter (Ruff for server/devtools, Biome for dashboard/landing)."""
    env = flags['env']
    module = flags.get('module', 'server')

    if module in FRONTEND_MODULES:
        _header(f'biome format [{env}] {module}')
        if not ensure_running(env):
            return 1
        _step(f'Ejecutando Biome format en {module}...')
        rc = _run_frontend_conformance(
            env,
            module=module,
            pkg_script='format',
        )
        if rc != 0:
            _err('Error ejecutando Biome format')
            return 1
        _ok('Formato aplicado')
        return 0

    # Python: ruff format en host.
    from pathlib import Path
    import subprocess

    from shared.paths import PROJECT_ROOT

    targets = _parse_files_flag(flags, module=module)
    _header(f'ruff format [host] {module}')

    ruff_bin = PROJECT_ROOT / 'devtools' / '.venv' / 'bin' / 'ruff'
    if not ruff_bin.exists():
        _err(f'No se encontro ruff en {ruff_bin}')
        return 1

    cwd = PROJECT_ROOT / module
    cmd = [str(ruff_bin), 'format', *targets]
    _step('Ejecutando Ruff format (host)...')
    result = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
    if result.returncode != 0:
        _err('Error ejecutando formatter')
        return 1
    _ok('Formato aplicado')
    return 0
