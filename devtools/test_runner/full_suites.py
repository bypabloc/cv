"""Full-suite execution path: run every test type for the requested modules.

This is the default mode (no ``--git-mode``) and the fallback for git-mode
when a module's classification yields no work to do. Each module delegates
to ``shared.test_executors`` (server) o al path genérico de frontend
(Vitest para apps Astro y packages) — y para ``devtools`` se invoca pytest
en el host Python 3.14, fuera de Docker.

Junio 2026: los E2E del portfolio (Playwright) ya no se corren aqui. Los
módulos/tipos ``feature``, ``e2e`` y ``tests`` fueron eliminados y se
corren con el comando dedicado ``python devtools/run.py e2e``.
"""

from __future__ import annotations

import subprocess
import sys

from shared.console import _err
from shared.console import _ok
from shared.console import _step
from shared.paths import DEVTOOLS_DIR
from shared.paths import PROJECT_ROOT
from shared.test_executors import run_dashboard_tests
from shared.test_executors import run_landing_tests
from shared.test_executors import run_server_tests

from test_runner.modules import resolve_types_for_module


def _run_devtools_tests(*, verbose: bool, quiet: bool) -> int:
    """Run devtools unit tests on the host (devtools/.venv, no Docker)."""
    venv_python = DEVTOOLS_DIR / '.venv' / 'bin' / 'python'
    if not venv_python.exists():
        _err(
            'devtools/.venv/bin/python no existe. '
            'Corre `python devtools/run.py docker setup` o `uv sync --project devtools`.',
        )
        return 1

    cmd = [
        str(venv_python),
        '-m',
        'pytest',
        'devtools/tests',
        '-c',
        'devtools/tests/pytest.ini',
    ]
    if verbose:
        cmd.append('-v')

    _step('Ejecutando devtools unit tests (host)...')
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=str(PROJECT_ROOT),
        check=False,
        timeout=180,
        capture_output=quiet,
        text=True,
    )
    if result.returncode != 0:
        if quiet and result.stdout:
            print(result.stdout)
        if quiet and result.stderr:
            print(result.stderr, file=sys.stderr)
        _err('Devtools unit tests fallaron')
        return 1

    _ok('Devtools unit tests pasaron')
    return 0


def execute_full_suites(
    *,
    modules: list[str],
    env: str,
    test_type: str,
    verbose: bool,
    quiet: bool,
) -> dict[str, int]:
    """Execute full test suites for each module x type combination."""
    results: dict[str, int] = {}

    _portfolio_apps = (
        'hub',
        'generic',
        'fintech',
        'architect',
        'leader',
        'vibe',
    )
    _portfolio_pkgs = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')
    _all_frontend = set(_portfolio_apps) | {f'pkg-{p}' for p in _portfolio_pkgs}

    for module in modules:
        types = resolve_types_for_module(test_type, module)
        for t in types:
            print()
            key = f'{module}:{t}'
            # Los E2E del portfolio (api/admin/app) NO se corren aqui: son
            # Python y viven en el comando dedicado `e2e`.
            if module == 'server':
                results[key] = run_server_tests(env, t, verbose, quiet=quiet)
            elif module in _all_frontend:
                # Apps Astro o packages: usar el path generico de frontend tests
                # (vitest run + coverage en cwd del módulo dentro del container).
                results[key] = _run_portfolio_frontend_tests(
                    env=env,
                    module=module,
                    test_type=t,
                    verbose=verbose,
                    quiet=quiet,
                )
            elif module == 'devtools':
                results[key] = _run_devtools_tests(
                    verbose=verbose,
                    quiet=quiet,
                )

    return results


def _run_portfolio_frontend_tests(
    *,
    env: str,
    module: str,
    test_type: str,
    verbose: bool,
    quiet: bool,
) -> int:
    """Ejecuta vitest/astro check para apps y packages del portfolio."""
    from shared.compose import compose_exec
    from shared.compose import is_service_running
    from shared.console import _err

    # Para packages, ejecutar dentro del container `generic` con cwd override.
    # Para apps, ejecutar en el container de la propia app.
    if module.startswith('pkg-'):
        pkg = module.removeprefix('pkg-')
        target_service = 'generic'
        target_workdir = f'/app/packages/{pkg}'
    else:
        target_service = module
        target_workdir = f'/app/apps/{module}'

    if not is_service_running(env, target_service):
        _err(
            f'Container {target_service} no esta corriendo. '
            f'Ejecuta: python devtools/run.py docker up --env={env}'
        )
        return 1

    if test_type == 'typecheck':
        cmd = ['pnpm', 'run', 'typecheck']
    elif test_type == 'coverage':
        cmd = ['pnpm', 'exec', 'vitest', 'run', '--coverage']
    else:  # unit
        cmd = ['pnpm', 'exec', 'vitest', 'run']

    result = compose_exec(
        env,
        target_service,
        cmd,
        workdir=target_workdir,
        timeout=300,
        capture=quiet,
    )
    if result.returncode != 0:
        if quiet and hasattr(result, 'stdout') and result.stdout:
            print(result.stdout)
        return result.returncode
    return 0
