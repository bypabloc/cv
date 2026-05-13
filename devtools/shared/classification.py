"""File classification with path mirroring for server, dashboard and landing.

Used by git hooks (_common.py) and test_runner to classify changed files
into source<->test mirror pairs and detect integration tests.

Files matching ``shared.coverage.SERVER_COVERAGE_EXCLUDES`` or
``FRONTEND_COVERAGE_EXCLUDES`` are filtered out of coverage pairs so
__init__.py, enums/, constants.py, migrations/ etc. don't trigger the
80% per-file coverage rule.
"""

from pathlib import Path

from shared.coverage import is_excluded_from_coverage


# Mirror conventions per frontend module.
#
# Portfolio monorepo:
#   apps/<APP>/src/<X>         -> apps/<APP>/tests/unit/<X>      (.astro -> .test.ts)
#   packages/<PKG>/src/<X>     -> packages/<PKG>/tests/unit/<X>  (.ts -> .test.ts)
#
# Las APPs son: hub, generic, fintech, architect, leader, vibe.
# Los PACKAGES son: app-shared, content, cv-pdf, seo, ui.


def _astro_app_layout(app_name: str) -> dict:
    """Layout para una app Astro: apps/<app>/src -> apps/<app>/tests/unit."""
    return {
        'source_prefixes': (f'apps/{app_name}/src/',),
        'test_prefix': f'apps/{app_name}/tests/unit/',
        'strip_for_mirror': f'apps/{app_name}/src/',
        'source_extensions': ('.ts', '.astro'),
        'test_extension': '.test.ts',
        'excluded_path_parts': (
            'node_modules/',
            '.astro/',
            'dist/',
            'coverage/',
        ),
    }


def _package_layout(pkg_name: str) -> dict:
    """Layout para un package compartido: packages/<pkg>/src -> packages/<pkg>/tests/unit."""
    return {
        'source_prefixes': (f'packages/{pkg_name}/src/',),
        'test_prefix': f'packages/{pkg_name}/tests/unit/',
        'strip_for_mirror': f'packages/{pkg_name}/src/',
        'source_extensions': ('.ts',),
        'test_extension': '.test.ts',
        'excluded_path_parts': (
            'node_modules/',
            'dist/',
            'coverage/',
        ),
    }


_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')

_FRONTEND_LAYOUT: dict[str, dict] = {}
for _app in _PORTFOLIO_APPS:
    _FRONTEND_LAYOUT[_app] = _astro_app_layout(_app)
for _pkg in _PORTFOLIO_PACKAGES:
    _FRONTEND_LAYOUT[f'pkg-{_pkg}'] = _package_layout(_pkg)


def classify_server_files(
    all_files: list[str],
    coverage_files: list[str],
    *,
    project_root: Path,
) -> dict:
    """Classify server files into source<->test mirror pairs.

    Returns:
        dict with keys:
            unit_pairs: list of (source, test) path tuples
            integration_test_files: list of integration test paths
            run_unit: bool - has source<->test pairs
            run_coverage: bool - alias for run_unit
            has_integration_files: bool - integration dir exists or has tests
            run_integration: bool - has integration tests in changeset
    """
    unit_pairs: list[tuple[str, str]] = []
    seen_tests: set[str] = set()

    for src in coverage_files:
        if is_excluded_from_coverage(src):
            continue
        key = src.removeprefix('server/')
        mirror = project_root / 'server' / 'tests' / 'unit' / 'src' / key
        if mirror.exists():
            mirror_rel = f'server/tests/unit/src/{key}'
            unit_pairs.append((src, mirror_rel))
            seen_tests.add(mirror_rel)

    for f in all_files:
        if not f.startswith('server/tests/unit/') or not f.endswith('.py'):
            continue
        if f in seen_tests:
            continue
        key = f.removeprefix('server/tests/unit/src/')
        source = f'server/{key}'
        if is_excluded_from_coverage(source):
            continue
        if (project_root / source).exists():
            unit_pairs.append((source, f))
            seen_tests.add(f)

    # `feature` reemplaza al historico `integration` (mayo 2026). Aceptamos
    # ambas paths para evitar romper checkouts antiguos durante la transicion;
    # el `feature/` es la fuente nueva.
    integration_tests = [
        f
        for f in all_files
        if f.startswith(
            ('server/tests/feature/', 'server/tests/integration/'),
        )
        and f.endswith('.py')
    ]

    feature_dir = project_root / 'server' / 'tests' / 'feature'
    integration_dir = project_root / 'server' / 'tests' / 'integration'
    has_integration = (
        bool(integration_tests)
        or (feature_dir.is_dir() and any(feature_dir.iterdir()))
        or (integration_dir.is_dir() and any(integration_dir.iterdir()))
    )

    has_pairs = bool(unit_pairs)

    return {
        'unit_pairs': unit_pairs,
        'integration_test_files': integration_tests,
        'integration_tests': integration_tests,
        'run_coverage': has_pairs,
        'run_unit': has_pairs,
        'has_integration_files': has_integration,
        'run_integration': bool(integration_tests),
    }


def _is_excluded_path(rel_path: str, excluded_parts: tuple[str, ...]) -> bool:
    """True if any excluded segment appears in rel_path."""
    return any(part in rel_path for part in excluded_parts)


def _build_test_path(source: str, layout: dict) -> str:
    """Compute the mirror test path for a given source path.

    Portfolio (Astro + packages):
        apps/<APP>/src/X/Y.ts     -> apps/<APP>/tests/unit/X/Y.test.ts
        apps/<APP>/src/X/Y.astro  -> apps/<APP>/tests/unit/X/Y.test.ts
        packages/<PKG>/src/X/Y.ts -> packages/<PKG>/tests/unit/X/Y.test.ts
    """
    relative = source.removeprefix(layout['strip_for_mirror'])
    p = Path(relative)
    test_ext = layout['test_extension']

    if test_ext == '.test.ts':
        # All portfolio modules: drop original suffix, append `.test.ts`.
        relative = f'{p.with_suffix("")}.test.ts'
    elif p.suffix in ('.vue', '.astro', '.tsx'):
        relative = str(p.with_suffix(test_ext))
    return f'{layout["test_prefix"]}{relative}'


def _resolve_test_to_source(
    test_path: str,
    layout: dict,
    project_root: Path,
) -> str | None:
    """Reverse mirror: given a test path, find an existing source on disk.

    Dashboard tests end in `.test.ts`; landing tests end in `.ts`. We probe
    each candidate source extension and return the first that exists.
    """
    relative = test_path.removeprefix(layout['test_prefix'])
    test_ext = layout['test_extension']

    if test_ext == '.test.ts' and relative.endswith('.test.ts'):
        base = relative[: -len('.test.ts')]
    else:
        base = str(Path(relative).with_suffix(''))

    parent_in_module = layout['strip_for_mirror']

    for ext in layout['source_extensions']:
        candidate = f'{parent_in_module}{base}{ext}'
        if (project_root / candidate).exists():
            return candidate

    return None


def _is_source_candidate(f: str, layout: dict) -> bool:
    """True if ``f`` is a frontend source file (not under tests, valid ext)."""
    if _is_excluded_path(f, layout['excluded_path_parts']):
        return False
    if not f.startswith(layout['source_prefixes']):
        return False
    if not f.endswith(layout['source_extensions']):
        return False
    return layout['test_prefix'] not in f


def _is_test_candidate(f: str, layout: dict) -> bool:
    """True if ``f`` is a frontend test file at the canonical mirror path."""
    if _is_excluded_path(f, layout['excluded_path_parts']):
        return False
    if not f.startswith(layout['test_prefix']):
        return False
    return f.endswith(layout['test_extension'])


def _classify_forward(
    files: list[str],
    layout: dict,
    project_root: Path,
) -> tuple[
    list[tuple[str, str]],
    list[tuple[str, str]],
    set[str],
    set[str],
]:
    """Forward pass: source -> mirror. Returns (pairs, missing, seen_t, seen_s)."""
    pairs: list[tuple[str, str]] = []
    missing: list[tuple[str, str]] = []
    seen_tests: set[str] = set()
    seen_sources: set[str] = set()

    for f in files:
        if not _is_source_candidate(f, layout):
            continue
        if is_excluded_from_coverage(f):
            continue
        test_path = _build_test_path(f, layout)
        if (project_root / test_path).exists():
            if test_path not in seen_tests:
                pairs.append((f, test_path))
                seen_tests.add(test_path)
                seen_sources.add(f)
        else:
            missing.append((f, test_path))

    return pairs, missing, seen_tests, seen_sources


def _classify_reverse(
    files: list[str],
    layout: dict,
    project_root: Path,
    seen_tests: set[str],
    seen_sources: set[str],
) -> list[tuple[str, str]]:
    """Reverse pass: test -> source on disk. Returns extra pairs."""
    extra: list[tuple[str, str]] = []
    for f in files:
        if not _is_test_candidate(f, layout):
            continue
        if f in seen_tests:
            continue
        source = _resolve_test_to_source(f, layout, project_root)
        if source and source not in seen_sources:
            extra.append((source, f))
            seen_tests.add(f)
            seen_sources.add(source)
    return extra


def classify_frontend_files(
    module: str,
    files: list[str],
    *,
    project_root: Path,
) -> dict:
    """Classify frontend files into source<->test mirror pairs.

    Mirror:
        app:     app/<X>           -> app/tests/unit/src/<X>
                 (X starts with 'app/' or 'stores/'; .vue maps to .ts)
        landing: landing/src/<X>   -> landing/tests/unit/src/<X>
                 (.astro maps to .ts)

    Returns:
        dict with keys:
            unit_pairs: list of (source, test) tuples (existing pairs)
            missing_mirrors: list of (source, expected_test) for sources
                without an existing mirror -- these MUST fail the hook
            run_coverage: bool - True iff unit_pairs is non-empty
    """
    if module not in _FRONTEND_LAYOUT:
        msg = f'Unknown frontend module: {module}'
        raise ValueError(msg)

    layout = _FRONTEND_LAYOUT[module]

    unit_pairs, missing, seen_tests, seen_sources = _classify_forward(
        files,
        layout,
        project_root,
    )
    unit_pairs.extend(
        _classify_reverse(
            files, layout, project_root, seen_tests, seen_sources
        ),
    )

    return {
        'unit_pairs': unit_pairs,
        'missing_mirrors': missing,
        'run_coverage': bool(unit_pairs),
    }
