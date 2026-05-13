"""Deletion mirror enforcement (orphan source/test detection).

Detecta dos clases de huerfanos cuando un changeset elimina archivos:

  - **Orphan test**: source eliminado pero su test mirror sigue en disco.
    El usuario debe eliminar también el test mirror.

  - **Orphan source**: test eliminado pero su source sigue en disco.
    El usuario debe restaurar el test (o eliminar también el source).

Se aplica solo al modo pre-push para no penalizar commits intermedios. Los
renames (delete + add) NO reciben tratamiento especial: si el usuario hace
``git mv source/foo.ts source/bar.ts`` debe mover también el test mirror,
o el hook lo bloqueara.

Path mirroring (portfolio Astro monorepo):
  - server: server/<X>.py                   -> server/tests/unit/src/<X>.py
  - apps Astro: apps/<APP>/src/<X>.{ts,astro}    -> apps/<APP>/tests/unit/<X>.test.ts
  - packages:   packages/<PKG>/src/<X>.ts        -> packages/<PKG>/tests/unit/<X>.test.ts

Excluye archivos cubiertos por SERVER_COVERAGE_EXCLUDES o
FRONTEND_COVERAGE_EXCLUDES (no requieren test mirror).
"""

from pathlib import Path

from shared.classification import _FRONTEND_LAYOUT
from shared.coverage import is_excluded_from_coverage


def _server_mirror_path(source: str) -> str:
    """Mirror path for a server source: server/X.py -> server/tests/unit/src/X.py."""
    key = source.removeprefix('server/')
    return f'server/tests/unit/src/{key}'


def _server_source_from_mirror(test_path: str) -> str:
    """Reverse: server/tests/unit/src/X.py -> server/X.py."""
    key = test_path.removeprefix('server/tests/unit/src/')
    return f'server/{key}'


def _is_server_source(path: str) -> bool:
    return (
        path.startswith('server/')
        and path.endswith('.py')
        and '/tests/' not in path
    )


def _is_server_test(path: str) -> bool:
    return path.startswith('server/tests/unit/src/') and path.endswith('.py')


def _frontend_mirror_path(module: str, source: str) -> str | None:
    """Build frontend test mirror path from a source path.

    Returns None if the path does not match a known source convention.
    """
    if module not in _FRONTEND_LAYOUT:
        return None
    layout = _FRONTEND_LAYOUT[module]

    if not source.startswith(layout['source_prefixes']):
        return None
    if not source.endswith(layout['source_extensions']):
        return None

    relative = source.removeprefix(layout['strip_for_mirror'])
    p = Path(relative)
    if p.suffix in ('.vue', '.astro'):
        relative = str(p.with_suffix(layout['test_extension']))
    return f'{layout["test_prefix"]}{relative}'


def _frontend_source_candidates_from_mirror(
    module: str,
    test_path: str,
) -> list[str]:
    """Reverse: candidate sources for a frontend mirror test path.

    Portfolio uses `.test.ts` mirrors. A test could correspond to a source
    with extensión .ts or .astro (apps) or .ts (packages). Returns all
    candidates and the caller probes which one exists on disk.
    """
    if module not in _FRONTEND_LAYOUT:
        return []
    layout = _FRONTEND_LAYOUT[module]

    if not test_path.startswith(layout['test_prefix']):
        return []
    # Portfolio mirror tests end in '.test.ts'.
    if not test_path.endswith('.test.ts'):
        return []

    relative = test_path.removeprefix(layout['test_prefix'])
    # Strip both `.test.ts` and any inner suffix to get the bare path.
    base = relative[: -len('.test.ts')]
    parent = layout['strip_for_mirror']
    return [f'{parent}{base}{ext}' for ext in layout['source_extensions']]


def _is_frontend_source(module: str, path: str) -> bool:
    if module not in _FRONTEND_LAYOUT:
        return False
    layout = _FRONTEND_LAYOUT[module]
    if path.startswith(layout['test_prefix']):
        return False
    return path.startswith(layout['source_prefixes']) and path.endswith(
        layout['source_extensions']
    )


def _is_frontend_test(module: str, path: str) -> bool:
    if module not in _FRONTEND_LAYOUT:
        return False
    layout = _FRONTEND_LAYOUT[module]
    return path.startswith(layout['test_prefix']) and path.endswith('.test.ts')


def _collect_server_orphans(
    deleted_server: list[str],
    deleted_set: set[str],
    project_root: Path,
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    orphan_tests: list[tuple[str, str, str]] = []
    orphan_sources: list[tuple[str, str, str]] = []

    for source in deleted_server:
        if not _is_server_source(source) or is_excluded_from_coverage(source):
            continue
        mirror = _server_mirror_path(source)
        if mirror in deleted_set:
            continue
        if (project_root / mirror).exists():
            orphan_tests.append(('server', source, mirror))

    for test in deleted_server:
        if not _is_server_test(test):
            continue
        source = _server_source_from_mirror(test)
        if source in deleted_set:
            continue
        if is_excluded_from_coverage(source):
            continue
        if (project_root / source).exists():
            orphan_sources.append(('server', test, source))

    return orphan_tests, orphan_sources


def _frontend_orphan_test_for(
    module: str,
    source: str,
    deleted_set: set[str],
    project_root: Path,
) -> tuple[str, str, str] | None:
    if not _is_frontend_source(module, source):
        return None
    if is_excluded_from_coverage(source):
        return None
    mirror = _frontend_mirror_path(module, source)
    if not mirror or mirror in deleted_set:
        return None
    if (project_root / mirror).exists():
        return (module, source, mirror)
    return None


def _frontend_orphan_source_for(
    module: str,
    test: str,
    deleted_set: set[str],
    project_root: Path,
) -> tuple[str, str, str] | None:
    if not _is_frontend_test(module, test):
        return None
    for source in _frontend_source_candidates_from_mirror(module, test):
        if source in deleted_set:
            return None
        if is_excluded_from_coverage(source):
            continue
        if (project_root / source).exists():
            return (module, test, source)
    return None


def _collect_frontend_orphans(
    module: str,
    deleted_module: list[str],
    deleted_set: set[str],
    project_root: Path,
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    orphan_tests: list[tuple[str, str, str]] = []
    orphan_sources: list[tuple[str, str, str]] = []

    for source in deleted_module:
        result = _frontend_orphan_test_for(
            module,
            source,
            deleted_set,
            project_root,
        )
        if result is not None:
            orphan_tests.append(result)

    for test in deleted_module:
        result = _frontend_orphan_source_for(
            module,
            test,
            deleted_set,
            project_root,
        )
        if result is not None:
            orphan_sources.append(result)

    return orphan_tests, orphan_sources


_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')


def collect_orphan_pairs(
    deleted_by_module: dict[str, list[str]],
    *,
    project_root: Path,
) -> dict[str, list[tuple[str, str, str]]]:
    """Detect orphans introduced by the changeset.

    Args:
        deleted_by_module: dict con keys 'server', '<app>' (cada app Astro)
            y 'pkg-<package>' (cada package). Valor: lista de paths
            eliminados en ese módulo.
        project_root: project root path (resolved).

    Returns:
        dict con:
            - orphan_tests:   [(module, deleted_source, surviving_test), ...]
            - orphan_sources: [(module, deleted_test, surviving_source), ...]
    """
    deleted_set: set[str] = set()
    for files in deleted_by_module.values():
        deleted_set.update(files)

    server_tests, server_sources = _collect_server_orphans(
        deleted_by_module.get('server', []),
        deleted_set,
        project_root,
    )

    orphan_tests = list(server_tests)
    orphan_sources = list(server_sources)

    frontend_modules = list(_PORTFOLIO_APPS) + [
        f'pkg-{p}' for p in _PORTFOLIO_PACKAGES
    ]
    for module in frontend_modules:
        mod_tests, mod_sources = _collect_frontend_orphans(
            module,
            deleted_by_module.get(module, []),
            deleted_set,
            project_root,
        )
        orphan_tests.extend(mod_tests)
        orphan_sources.extend(mod_sources)

    return {
        'orphan_tests': orphan_tests,
        'orphan_sources': orphan_sources,
    }


def classify_deleted_files(deleted_paths: list[str]) -> dict[str, list[str]]:
    """Classify deleted paths into {server, <app>, pkg-<package>}.

    Devtools deletes are intentionally excluded (no mirror requirement).
    """
    result: dict[str, list[str]] = {
        'server': [
            f
            for f in deleted_paths
            if f.startswith('server/') and f.endswith('.py')
        ],
    }

    for app in _PORTFOLIO_APPS:
        prefix = f'apps/{app}/'
        result[app] = [
            f
            for f in deleted_paths
            if f.startswith(prefix) and f.endswith(('.ts', '.astro'))
        ]

    for pkg in _PORTFOLIO_PACKAGES:
        prefix = f'packages/{pkg}/'
        result[f'pkg-{pkg}'] = [
            f
            for f in deleted_paths
            if f.startswith(prefix) and f.endswith('.ts')
        ]

    return result
