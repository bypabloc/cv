"""Git-mode execution path: scan changed files, run only what's affected.

Uses the project's path-mirroring rules to map source files to their unit
tests, runs each pair through pytest with per-file coverage, and runs any
integration tests directly. Frontend modules currently fall back to full
suites in git-mode (Vitest path-mirroring is not wired up yet).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from shared.classification import classify_server_files
from shared.commands import build_pytest_integration_cmd
from shared.commands import build_pytest_unit_coverage_cmd
from shared.commands import prepare_unit_coverage_args
from shared.compose import compose_exec
from shared.console import _err
from shared.console import _ok
from shared.console import _step
from shared.console import _warn
from shared.coverage import COVERAGE_THRESHOLD
from shared.coverage import format_coverage_line
from shared.coverage import verify_server_coverage
from shared.paths import PROJECT_ROOT
from shared.test_executors import _print_captured_output

from test_runner.git_mode_scan import get_changed_files
from test_runner.git_mode_scan import get_coverage_files
from test_runner.modules import resolve_types_for_module


def _classify_server(
    all_files: list[str],
    coverage_files: list[str],
) -> dict[str, Any]:
    """Classify server files into unit pairs / integration tests / coverage."""
    return classify_server_files(
        all_files,
        coverage_files,
        project_root=PROJECT_ROOT,
    )


def _check_server_coverage(unit_pairs: list[tuple[str, str]]) -> int:
    """Verify per-file coverage from coverage.json. 0=OK, 1=FAIL."""
    passed, failed = verify_server_coverage(
        unit_pairs,
        project_root=PROJECT_ROOT,
        threshold=COVERAGE_THRESHOLD,
    )
    for entry in passed + failed:
        print(format_coverage_line(entry))

    if failed:
        print(f'\n{len(failed)} archivo(s) bajo {COVERAGE_THRESHOLD}%:')
        for f in failed:
            print(f'  - {f["source"]}: {f["pct"]:.1f}%')
        _err('Server coverage per-file FALLO')
        return 1

    return 0


def _run_server_unit_coverage(
    unit_pairs: list[tuple[str, str]],
    *,
    env: str,
    quiet: bool,
) -> int:
    """Run server unit tests with per-file coverage via Docker."""
    _step(f'Server unit tests + coverage ({len(unit_pairs)} par(es))...')

    if not quiet:
        for source, test in unit_pairs:
            print(f'    {source} -> {test}')

    for cov_file in ['server/.coverage', 'server/coverage.json']:
        cov_path = PROJECT_ROOT / cov_file
        if cov_path.exists():
            cov_path.unlink()

    test_keys, cov_args = prepare_unit_coverage_args(unit_pairs)
    cmd = build_pytest_unit_coverage_cmd(test_keys, cov_args)

    result = compose_exec(env, 'server', cmd, timeout=300, capture=quiet)

    if result.returncode != 0:
        if quiet and hasattr(result, 'stdout'):
            _print_captured_output(result)
        _err('Server unit tests fallaron')
        return 1

    rc = _check_server_coverage(unit_pairs)
    if rc != 0:
        return rc

    _ok('Server unit tests + coverage')
    return 0


def _run_server_integration_files(
    integration_tests: list[str],
    *,
    env: str,
    quiet: bool,
) -> int:
    """Run specific server integration test files via Docker."""
    _step(f'Server integration tests ({len(integration_tests)} archivo(s))...')

    int_keys = [f.removeprefix('server/') for f in integration_tests]
    cmd = build_pytest_integration_cmd(int_keys)

    result = compose_exec(env, 'server', cmd, timeout=600, capture=quiet)

    if result.returncode != 0:
        if quiet and hasattr(result, 'stdout'):
            _print_captured_output(result)
        _err('Server integration tests fallaron')
        return 1

    _ok('Server integration tests')
    return 0


def _dispatch_git_type(
    *,
    module: str,
    test_type: str,
    has_files: bool,
    run_fn: Callable[[], int],
    verbose: bool,
    skip_label: str,
    results: dict[str, int],
) -> None:
    """Dispatch a single test type in git-mode: run it or mark as skipped."""
    key = f'{module}:{test_type}'
    if has_files:
        print()
        results[key] = run_fn()
    elif verbose:
        _warn(f'{module}: {skip_label}')
        results[key] = -1


def _execute_server_git_mode(
    *,
    env: str,
    test_type: str,
    git_mode: str,
    verbose: bool,
    quiet: bool,
) -> dict[str, int]:
    """Classify server files and run the relevant tests."""
    results: dict[str, int] = {}

    all_files = get_changed_files(module='server', git_mode=git_mode)
    if not all_files:
        if verbose:
            _warn(f'server: sin archivos cambiados (git-mode={git_mode})')
        results['server'] = -1
        return results

    coverage_files = get_coverage_files(git_mode=git_mode)
    classification = _classify_server(all_files, coverage_files)
    types = resolve_types_for_module(test_type, 'server')

    def unit_runner() -> int:
        return _run_server_unit_coverage(
            classification['unit_pairs'],
            env=env,
            quiet=quiet,
        )

    def int_runner() -> int:
        return _run_server_integration_files(
            classification['integration_tests'],
            env=env,
            quiet=quiet,
        )

    type_config = [
        (
            'coverage',
            classification['run_unit'],
            unit_runner,
            'sin pares source<->test mirror para coverage',
        ),
        (
            'unit',
            classification['run_unit'],
            unit_runner,
            'sin pares source<->test mirror para unit',
        ),
        (
            'integration',
            classification['run_integration'],
            int_runner,
            'sin archivos de integration tests cambiados',
        ),
    ]

    for t, has_files, runner, skip_label in type_config:
        if t in types:
            _dispatch_git_type(
                module='server',
                test_type=t,
                has_files=has_files,
                run_fn=runner,
                verbose=verbose,
                skip_label=skip_label,
                results=results,
            )

    return results


def execute_git_mode(
    *,
    modules: list[str],
    env: str,
    test_type: str,
    git_mode: str,
    verbose: bool,
    quiet: bool,
    full_suite_runner: Callable[..., dict[str, int]],
) -> dict[str, int]:
    """Execute tests using path mirroring and per-file coverage.

    Frontend modules (dashboard, landing) currently fall back to full-suite
    execution because per-file coverage path-mirroring is not wired up
    for Vitest yet. The caller passes ``full_suite_runner`` to avoid an
    import cycle with ``full_suites.py``.
    """
    results: dict[str, int] = {}

    if 'server' in modules:
        results.update(
            _execute_server_git_mode(
                env=env,
                test_type=test_type,
                git_mode=git_mode,
                verbose=verbose,
                quiet=quiet,
            )
        )

    for frontend in ('dashboard', 'landing'):
        if frontend in modules:
            if verbose:
                _warn(
                    f'{frontend}: git-mode no soporta per-file coverage; '
                    f'cayendo a suite completa.',
                )
            full_results = full_suite_runner(
                modules=[frontend],
                env=env,
                test_type=test_type,
                verbose=verbose,
                quiet=quiet,
            )
            results.update(full_results)

    return results
