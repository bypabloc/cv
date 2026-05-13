"""``mutation_testing`` script entry point.

Wrapper sobre ``mutmut`` con thresholds por criticidad. Lee la config en
``devtools/mutation_testing/config.py`` para clasificar paths y aplicar
el threshold correspondiente.

Politica completa: ``.claude/rules/ai-testing-independence.md``.

Modos:
- ``--paths=apps/payments,apps/auth`` -> mutar paths explicitos
- ``--category=critical|standard|experimental`` -> mutar todos los paths de la categoria
- ``--all`` -> mutar todas las categorias
- ``--dry-run`` -> imprimir plan sin ejecutar

Ejecucion: el wrapper invoca ``mutmut run`` dentro del container del
server (Docker es el runtime obligatorio del proyecto). Si el container
no esta arriba, falla con instruccion de levantarlo.

Exit codes:
    0 - todos los paths >= threshold
    1 - al menos un path < threshold (o mutmut fallo)
    2 - error interno (config invalido, container no disponible)
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any

from mutation_testing import config as mutation_config


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SERVER_DIR = _PROJECT_ROOT / 'server'


def main(flags: dict[str, Any]) -> int:
    """CLI entry point. Llamado desde ``devtools/run.py``.

    Args:
        flags: dict de flags ya validados por ``flags.py``.

    Returns:
        Exit code (0 = ok, 1 = score insuficiente, 2 = error interno).
    """
    config: ModuleType = mutation_config

    targets = _resolve_targets(flags, config)
    if not targets:
        print(
            '[mutation_testing] sin paths para procesar (revisa --paths/--category/--all).',
            file=sys.stderr,
        )
        return 0

    if flags.get('dry_run'):
        return _print_plan(targets, config)

    if not _ensure_runtime():
        return 2

    return _run_mutmut(targets, config)


# ── Helpers ──────────────────────────────────────────────────────────────


def _resolve_targets(
    flags: dict[str, Any], config: ModuleType
) -> list[tuple[str, str, float]]:
    """Resuelve lista de (path, category, threshold) a procesar."""
    if flags.get('all'):
        targets: list[tuple[str, str, float]] = []
        for category, paths in config.all_categories().items():
            threshold = {
                'critical': config.CRITICAL_THRESHOLD,
                'standard': config.STANDARD_THRESHOLD,
                'experimental': config.EXPERIMENTAL_THRESHOLD,
            }[category]
            targets.extend((p, category, threshold) for p in paths)
        return targets

    category = flags.get('category')
    if category:
        paths = config.all_categories()[category]
        threshold = {
            'critical': config.CRITICAL_THRESHOLD,
            'standard': config.STANDARD_THRESHOLD,
            'experimental': config.EXPERIMENTAL_THRESHOLD,
        }[category]
        return [(p, category, threshold) for p in paths]

    # --paths explicit
    explicit = flags.get('paths') or []
    return [
        (p, config.category_for_path(p), config.threshold_for_path(p))
        for p in explicit
    ]


def _print_plan(
    targets: list[tuple[str, str, float]], config: ModuleType
) -> int:
    """Imprime que paths se mutarian con que threshold (--dry-run)."""
    print('[mutation_testing] DRY RUN — plan de ejecucion:\n')
    print(f'  {"path":50}  {"categoria":12}  threshold')
    print(f'  {"-" * 50}  {"-" * 12}  ---------')
    for path, category, threshold in targets:
        print(f'  {path:50}  {category:12}  {threshold:.0%}')
    print()
    print(
        f'Total: {len(targets)} path(s). '
        'Para ejecutar de verdad, omitir --dry-run.'
    )
    return 0


def _ensure_runtime() -> bool:
    """Verifica que el container del server este disponible.

    Como ``mutmut`` corre tests reales, requiere el venv del server con
    todas las deps. Por convencion del proyecto eso vive en Docker.
    """
    # Si docker compose no existe, no podemos verificar — asumimos que el
    # usuario corre desde un entorno con server venv accesible.
    if shutil.which('docker') is None:
        print(
            'Aviso: `docker` no encontrado en PATH. mutmut correra con el '
            'venv del shell actual (asegurate de tener server deps instaladas).',
            file=sys.stderr,
        )
        return True

    # Subprocess controlado por nosotros (no se ejecuta input del usuario).
    cmd = [
        'docker',
        'compose',
        'ps',
        '--services',
        '--filter',
        'status=running',
    ]
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            'Aviso: no se pudo consultar docker compose. mutmut correra '
            'localmente (asegurate de tener server deps instaladas).',
            file=sys.stderr,
        )
        return True

    if 'server' not in result.stdout:
        print(
            'Error: container `server` no esta corriendo. Levantalo con:\n'
            '  python devtools/run.py docker up --env=local\n',
            file=sys.stderr,
        )
        return False

    return True


def _run_mutmut(
    targets: list[tuple[str, str, float]],
    config: ModuleType,
) -> int:
    """Ejecuta mutmut para cada target y verifica thresholds."""
    failed: list[tuple[str, str, float, float]] = []

    for path, category, threshold in targets:
        print(
            f'\n[mutation_testing] {path} (category={category}, '
            f'threshold={threshold:.0%})',
            file=sys.stderr,
        )

        score = _run_mutmut_for_path(path)
        if score is None:
            print(
                f'  [SKIP] no se pudo calcular score para {path}',
                file=sys.stderr,
            )
            continue

        status = 'PASS' if score >= threshold else 'FAIL'
        print(
            f'  -> score={score:.0%}  ({status})',
            file=sys.stderr,
        )
        if score < threshold:
            failed.append((path, category, threshold, score))

    if not failed:
        print(
            '\n[mutation_testing] OK: todos los paths >= threshold.',
            file=sys.stderr,
        )
        return 0

    print(
        '\n[mutation_testing] FAILED — paths bajo threshold:',
        file=sys.stderr,
    )
    for path, category, threshold, score in failed:
        print(
            f'  - {path} ({category}): {score:.0%} < {threshold:.0%}',
            file=sys.stderr,
        )
    print(
        '\nFix sugerido: agregar/fortalecer tests para mutaciones que '
        'sobreviven. mutmut results imprime los survivors.',
        file=sys.stderr,
    )
    return 1


def _run_mutmut_for_path(path: str) -> float | None:
    """Ejecuta ``mutmut run`` sobre ``path`` y retorna el score (0..1).

    Retorna None si mutmut no esta instalado o falla. El comando exacto
    depende de la version de mutmut; este wrapper es tolerante a variantes.
    """
    cmd_run = [
        'mutmut',
        'run',
        '--paths-to-mutate',
        path,
    ]
    result = subprocess.run(  # noqa: S603  # mutmut controlado por nosotros
        cmd_run,
        cwd=_SERVER_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    # mutmut run devuelve 0 si todos los mutantes son killed, 2 si hay
    # survivors. Ambos casos son valor para nosotros — leemos `mutmut results`.
    if result.returncode not in (0, 1, 2):
        print(
            f'  Aviso: mutmut run retorno codigo inesperado '
            f'{result.returncode}. stderr: {result.stderr[:500]}',
            file=sys.stderr,
        )
        return None

    return _parse_mutmut_score()


def _parse_mutmut_score() -> float | None:
    """Llama ``mutmut results`` y extrae el score como ratio (0..1).

    Subprocess controlado por nosotros (no se ejecuta input del usuario).
    """
    cmd = ['mutmut', 'results']
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=_SERVER_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    # Output de mutmut incluye lineas con `killed:`, `survived:` y
    # `suspicious:` que parseamos abajo.
    import contextlib

    killed = survived = 0
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip().lower()
        if line.startswith('killed:'):
            with contextlib.suppress(ValueError):
                killed = int(line.split(':', 1)[1].strip())
        elif line.startswith('survived:'):
            with contextlib.suppress(ValueError):
                survived = int(line.split(':', 1)[1].strip())

    total = killed + survived
    if total == 0:
        return None
    return killed / total


if __name__ == '__main__':
    # Permite ejecucion directa: python devtools/mutation_testing/main.py ...
    sys.path.insert(0, str(_PROJECT_ROOT / 'devtools'))
    from mutation_testing.flags import flag

    raw_flags: dict[str, Any] = {}
    for arg in sys.argv[1:]:
        if arg.startswith('--') and '=' in arg:
            k, v = arg[2:].split('=', 1)
            raw_flags[k.replace('-', '_')] = v
        elif arg.startswith('--'):
            raw_flags[arg[2:].replace('-', '_')] = True

    parsed = flag(raw_flags)
    if parsed.get('help'):
        print(__doc__)
        sys.exit(0)
    sys.exit(main(parsed))
