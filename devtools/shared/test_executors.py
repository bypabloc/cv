"""Test execution helpers shared by docker and test_runner scripts.

Runs server (pytest), dashboard (Vitest/typecheck) and landing (Vitest/typecheck)
tests inside their docker containers via ``compose_exec``. Centralized here
so ``docker.quality`` and ``test_runner`` share identical semantics:
capture-on-quiet, per-file coverage threshold check, frontend purity guard
(no .js files in src/app).
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from shared.compose import compose_exec
from shared.console import err
from shared.console import ok
from shared.console import step
from shared.paths import PROJECT_ROOT


COVERAGE_THRESHOLD = 80


# Scripts package.json mapping per frontend module.
# dashboard/landing share Vitest, but the typecheck script differs: Nuxt
# exposes ``typecheck`` while Astro uses ``check`` (astro check).
FRONTEND_TEST_SCRIPTS: dict[str, dict[str, str]] = {
    'dashboard': {
        'unit': 'test',
        'coverage': 'test:coverage',
        'typecheck': 'typecheck',
    },
    'landing': {
        'unit': 'test',
        'coverage': 'test:coverage',
        'typecheck': 'check',
    },
}


def _print_captured_output(
    result: subprocess.CompletedProcess[str],
) -> None:
    """Print captured stdout/stderr from a subprocess result."""
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def frontend_script(module: str, test_type: str) -> str | None:
    """Resolve the package.json script for a frontend module + test type."""
    return FRONTEND_TEST_SCRIPTS.get(module, {}).get(test_type)


def frontend_test_types(module: str) -> list[str]:
    """List supported test types for a frontend module."""
    return list(FRONTEND_TEST_SCRIPTS.get(module, {}))


def _resolve_module_src_dirs(module: str) -> list[Path]:
    """Resuelve directorios src para un module name del portfolio.

    Acepta:
      - Astro app: 'hub', 'generic', 'fintech', 'architect', 'leader', 'vibe'
        -> [apps/<X>/src]
      - Package: 'pkg-<name>' -> [packages/<name>/src]
      - Legacy: cualquier otro string se interpreta como path relativo
        (compat con codigo del fuente que pasa 'dashboard'/'landing').
    """
    portfolio_apps = (
        'hub',
        'generic',
        'fintech',
        'architect',
        'leader',
        'vibe',
    )
    if module in portfolio_apps:
        return [PROJECT_ROOT / 'apps' / module / 'src']
    if module.startswith('pkg-'):
        pkg = module.removeprefix('pkg-')
        return [PROJECT_ROOT / 'packages' / pkg / 'src']
    # Legacy: paths relativos
    return [
        PROJECT_ROOT / module / 'src',
        PROJECT_ROOT / module / 'app',
    ]


def check_no_js_files(module_root: str) -> list[str]:
    """Check que no haya archivos .js en el src del module.

    Returns the list of offenders (empty list = OK).
    """
    candidates = _resolve_module_src_dirs(module_root)
    js_files: list[str] = []
    for src in candidates:
        if not src.is_dir():
            continue
        js_files.extend(
            str(p.relative_to(PROJECT_ROOT)) for p in src.rglob('*.js')
        )
    return js_files


def verify_server_per_file_coverage(*, verbose: bool = False) -> int:
    """Verify per-file coverage from coverage.json.

    Returns 0 if every file is at or above ``COVERAGE_THRESHOLD``, 1 otherwise.
    """
    coverage_json = PROJECT_ROOT / 'server' / 'coverage.json'
    if not coverage_json.exists():
        err('No se genero coverage.json')
        return 1

    data = json.loads(coverage_json.read_text())
    files_data = data.get('files', {})
    failed: list[str] = []

    for file_key, file_info in sorted(files_data.items()):
        pct = file_info.get('summary', {}).get('percent_covered', 0)
        status = 'OK' if pct >= COVERAGE_THRESHOLD else 'FAIL'

        if pct < COVERAGE_THRESHOLD:
            failed.append(f'{file_key}: {pct:.1f}%')
        elif verbose:
            print(f'  {file_key:60s} {pct:6.1f}%  {status}')

    if failed:
        for f in failed:
            print(f'  FAIL  {f}')
        err(f'{len(failed)} archivo(s) bajo {COVERAGE_THRESHOLD}%')
        return 1

    ok(f'Coverage per-file: todos los archivos >= {COVERAGE_THRESHOLD}%')
    return 0


def run_server_tests(
    env: str,
    test_type: str,
    verbose: bool,
    *,
    quiet: bool = False,
) -> int:
    """Run server tests inside the server container.

    ``test_type`` of ``coverage`` triggers the per-file >= 80% verification;
    other types delegate to ``server/tests/run.py``.
    """
    if test_type == 'coverage':
        return _run_server_coverage(env, verbose=verbose, quiet=quiet)

    cmd = ['python', 'tests/run.py', f'--type={test_type}']
    if verbose:
        cmd.append('--verbose')

    should_capture = not verbose
    step(f'Ejecutando tests server {test_type}...')
    result = compose_exec(
        env,
        'server',
        cmd,
        timeout=600,
        capture=should_capture,
    )

    if result.returncode != 0:
        if should_capture:
            _print_captured_output(result)
        err(f'Tests server {test_type} fallaron')
        return 1

    ok(f'Tests server {test_type} pasaron')
    return 0


def _run_server_coverage(
    env: str,
    *,
    verbose: bool,
    quiet: bool,
) -> int:
    """Run server unit tests with per-file coverage verification."""
    cov_json = PROJECT_ROOT / 'server' / 'coverage.json'
    if cov_json.exists():
        cov_json.unlink()

    cmd = [
        'python',
        '-m',
        'pytest',
        'tests/',
        '-m',
        'unit',
        '--cov',
        '--cov-config=.coveragerc',
        '--cov-report=json:coverage.json',
        '--no-header',
        '--override-ini=addopts=--import-mode=importlib '
        '--disable-warnings --tb=short --strict-markers',
    ]
    if verbose:
        cmd.extend(['--cov-report=term-missing', '-v'])
    else:
        cmd.extend(['--cov-report=', '-q'])

    should_capture = not verbose
    step('Ejecutando tests server coverage (per-file >= 80%)...')
    result = compose_exec(
        env,
        'server',
        cmd,
        timeout=600,
        capture=should_capture,
    )

    if result.returncode != 0:
        if should_capture:
            _print_captured_output(result)
        err('Tests server coverage fallaron')
        return 1

    rc = verify_server_per_file_coverage(verbose=verbose)
    if rc != 0:
        return rc

    ok('Tests server coverage pasaron (per-file >= 80%)')
    return 0


def run_frontend_tests(
    env: str,
    *,
    module: str,
    test_type: str,
    verbose: bool,
    quiet: bool = False,
) -> int:
    """Run Vitest/typecheck tests inside a frontend container (dashboard, landing)."""
    js_files = check_no_js_files(module)
    if js_files:
        err(
            f'{module}/ contiene {len(js_files)} archivo(s) .js (solo .ts permitido):',
        )
        for f in js_files:
            print(f'  - {f}')
        return 1

    pkg_script = frontend_script(module, test_type)
    if not pkg_script:
        valid = ', '.join(sorted(frontend_test_types(module)))
        err(
            f'Tipo de test invalido para {module}: {test_type}. Validos: {valid}',
        )
        return 1

    # Vitest-based scripts: pass --passWithNoTests so the runner does not
    # fail when a frontend module has no tests yet. pnpm forwards extra args
    # after the script name directly (no `--` separator needed).
    cmd = ['pnpm', 'run', pkg_script]
    if test_type in {'unit', 'coverage'}:
        cmd.append('--passWithNoTests')

    should_capture = not verbose
    step(f'Ejecutando tests {module} {test_type}...')
    result = compose_exec(
        env,
        module,
        cmd,
        timeout=300,
        capture=should_capture,
    )

    if result.returncode != 0:
        if should_capture:
            _print_captured_output(result)
        err(f'Tests {module} {test_type} fallaron')
        return 1

    ok(f'Tests {module} {test_type} pasaron')
    return 0


def run_dashboard_tests(
    env: str,
    test_type: str,
    verbose: bool,
    *,
    quiet: bool = False,
) -> int:
    """Run dashboard (Nuxt) tests."""
    return run_frontend_tests(
        env,
        module='dashboard',
        test_type=test_type,
        verbose=verbose,
        quiet=quiet,
    )


def run_landing_tests(
    env: str,
    test_type: str,
    verbose: bool,
    *,
    quiet: bool = False,
) -> int:
    """Run landing (Astro) tests."""
    return run_frontend_tests(
        env,
        module='landing',
        test_type=test_type,
        verbose=verbose,
        quiet=quiet,
    )
