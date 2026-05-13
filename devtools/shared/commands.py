"""Test command builders for pytest and vitest.

Single source of truth for pytest/vitest command construction.
Used by git hooks and test_runner.
"""

from pathlib import Path


_PYTEST_OVERRIDES = (
    '--override-ini=addopts='
    '--import-mode=importlib '
    '--disable-warnings --tb=short --strict-markers'
)


def build_pytest_unit_coverage_cmd(
    test_keys: list[str],
    cov_args: list[str],
) -> list[str]:
    """Build pytest command for unit tests with per-file coverage."""
    return [
        'python',
        '-m',
        'pytest',
        *test_keys,
        '-c',
        'pytest.ini',
        '-m',
        'unit',
        *cov_args,
        '--cov-report=json:coverage.json',
        '--cov-fail-under=0',
        '--no-header',
        '-q',
        _PYTEST_OVERRIDES,
    ]


def build_pytest_integration_cmd(
    test_keys: list[str] | None = None,
) -> list[str]:
    """Build pytest command for feature tests (renombrado de integration).

    Mantenemos el nombre de la función ``build_pytest_integration_cmd``
    para no romper los hooks que la importan; el marker pytest cambia
    de ``integration`` a ``feature`` (mayo 2026) y el target default
    pasa de ``tests/`` a ``tests/feature/``.
    """
    targets = test_keys or ['tests/feature/']
    return [
        'python',
        '-m',
        'pytest',
        *targets,
        '-c',
        'pytest.ini',
        '-m',
        'feature',
        '--no-header',
        '-q',
    ]


def build_vitest_coverage_cmd(
    src_includes: list[str],
    test_files: list[str],
) -> list[str]:
    """Build vitest command for unit tests with per-file coverage.

    Uses --coverage.include to restrict the coverage report to the changed
    sources, and json-summary so the result can be parsed per-file.

    Args:
        src_includes: Source files to include in the coverage report (paths
            relative to the module workdir).
        test_files: Specific test files to execute (paths relative to the
            module workdir).
    """
    cmd = [
        'pnpm',
        'exec',
        'vitest',
        'run',
        *test_files,
        '--coverage',
        '--coverage.reporter=text',
        '--coverage.reporter=json-summary',
        '--coverage.thresholds.statements=0',
        '--coverage.thresholds.branches=0',
        '--coverage.thresholds.functions=0',
        '--coverage.thresholds.lines=0',
    ]

    cmd.extend(f'--coverage.include={include}' for include in src_includes)

    return cmd


def prepare_unit_coverage_args(
    unit_pairs: list[tuple[str, str]],
    *,
    prefix: str = 'server/',
) -> tuple[list[str], list[str]]:
    """Prepare test keys and coverage args from unit pairs.

    Returns:
        (test_keys, cov_args) ready for build_pytest_unit_coverage_cmd.
    """
    test_keys = [t.removeprefix(prefix) for _, t in unit_pairs]
    source_dirs = sorted(
        {str(Path(s.removeprefix(prefix)).parent) for s, _ in unit_pairs}
    )
    cov_args = [f'--cov={d}' for d in source_dirs]
    return test_keys, cov_args
