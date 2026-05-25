"""Unit tests for shared.deletion_mirror.

Path mirroring: devtools/shared/deletion_mirror.py -> este archivo.

Portfolio mirroring (server + apps Astro + packages):
  server:    server/<X>.py            -> server/tests/unit/src/<X>.py
  apps:      apps/<APP>/src/<X>.{ts,astro} -> apps/<APP>/tests/unit/<X>.test.ts
  packages:  packages/<PKG>/src/<X>.ts     -> packages/<PKG>/tests/unit/<X>.test.ts
"""

from pathlib import Path

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# classify_deleted_files
# ---------------------------------------------------------------------------


class TestClassifyDeletedFiles:
    """Clasifica una lista plana de paths eliminados por modulo."""

    def test_classifies_server_python_files(self):
        from shared.deletion_mirror import classify_deleted_files

        result = classify_deleted_files(
            [
                'server/apps/foo/services/bar.py',
                'server/tests/unit/src/apps/foo/services/bar.py',
            ]
        )

        assert result['server'] == [
            'server/apps/foo/services/bar.py',
            'server/tests/unit/src/apps/foo/services/bar.py',
        ]
        assert result['generic'] == []
        assert result['pkg-content'] == []

    def test_classifies_app_ts_and_astro(self):
        from shared.deletion_mirror import classify_deleted_files

        result = classify_deleted_files(
            [
                'apps/generic/src/lib/foo.ts',
                'apps/generic/src/components/Hero.astro',
            ]
        )

        assert result['generic'] == [
            'apps/generic/src/lib/foo.ts',
            'apps/generic/src/components/Hero.astro',
        ]
        assert result['server'] == []
        assert result['pkg-content'] == []

    def test_classifies_package_ts(self):
        from shared.deletion_mirror import classify_deleted_files

        result = classify_deleted_files(
            [
                'packages/content/src/schemas.ts',
                'packages/content/src/index.ts',
            ]
        )

        assert result['pkg-content'] == [
            'packages/content/src/schemas.ts',
            'packages/content/src/index.ts',
        ]
        assert result['server'] == []
        assert result['generic'] == []

    def test_ignores_non_relevant_extensions(self):
        from shared.deletion_mirror import classify_deleted_files

        result = classify_deleted_files(
            [
                'README.md',
                'docker/Dockerfile',
                'apps/generic/package.json',
                'devtools/shared/foo.py',
            ]
        )

        # Solo verificamos que TODAS las listas (server + apps + packages)
        # esten vacias para extensiones no relevantes.
        assert all(v == [] for v in result.values())


# ---------------------------------------------------------------------------
# collect_orphan_pairs - server
# ---------------------------------------------------------------------------


def _make_file(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('')


def _empty_module_map() -> dict[str, list[str]]:
    """Base dict con todos los modulos vacios + server."""
    apps = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
    pkgs = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')
    base: dict[str, list[str]] = {'server': []}
    for app in apps:
        base[app] = []
    for pkg in pkgs:
        base[f'pkg-{pkg}'] = []
    return base


class TestCollectOrphanPairsServer:
    """Detecta huerfanos cuando solo se elimina un lado del par server."""

    def test_orphan_test_when_source_deleted_and_mirror_remains(
        self,
        tmp_path,
    ):
        from shared.deletion_mirror import collect_orphan_pairs

        _make_file(
            tmp_path,
            'server/tests/unit/src/apps/foo/services/bar.py',
        )

        deleted = _empty_module_map()
        deleted['server'] = ['server/apps/foo/services/bar.py']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_tests'] == [
            (
                'server',
                'server/apps/foo/services/bar.py',
                'server/tests/unit/src/apps/foo/services/bar.py',
            )
        ]
        assert result['orphan_sources'] == []

    def test_orphan_source_when_test_deleted_and_source_remains(
        self,
        tmp_path,
    ):
        from shared.deletion_mirror import collect_orphan_pairs

        _make_file(tmp_path, 'server/apps/foo/services/bar.py')

        deleted = _empty_module_map()
        deleted['server'] = ['server/tests/unit/src/apps/foo/services/bar.py']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_sources'] == [
            (
                'server',
                'server/tests/unit/src/apps/foo/services/bar.py',
                'server/apps/foo/services/bar.py',
            )
        ]
        assert result['orphan_tests'] == []

    def test_no_orphan_when_both_sides_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        deleted = _empty_module_map()
        deleted['server'] = [
            'server/apps/foo/services/bar.py',
            'server/tests/unit/src/apps/foo/services/bar.py',
        ]

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_tests'] == []
        assert result['orphan_sources'] == []

    def test_excluded_paths_do_not_trigger_orphan(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        # __init__.py esta en SERVER_COVERAGE_EXCLUDES
        _make_file(tmp_path, 'server/tests/unit/src/apps/foo/__init__.py')

        deleted = _empty_module_map()
        deleted['server'] = ['server/apps/foo/__init__.py']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_tests'] == []
        assert result['orphan_sources'] == []


# ---------------------------------------------------------------------------
# collect_orphan_pairs - app Astro
# ---------------------------------------------------------------------------


class TestCollectOrphanPairsApp:
    """Detecta huerfanos en apps/<APP>/."""

    def test_orphan_test_when_ts_source_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        _make_file(tmp_path, 'apps/generic/tests/unit/lib/foo.test.ts')

        deleted = _empty_module_map()
        deleted['generic'] = ['apps/generic/src/lib/foo.ts']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_tests'] == [
            (
                'generic',
                'apps/generic/src/lib/foo.ts',
                'apps/generic/tests/unit/lib/foo.test.ts',
            )
        ]

    def test_orphan_source_when_ts_test_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        _make_file(tmp_path, 'apps/generic/src/lib/foo.ts')

        deleted = _empty_module_map()
        deleted['generic'] = ['apps/generic/tests/unit/lib/foo.test.ts']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_sources'] == [
            (
                'generic',
                'apps/generic/tests/unit/lib/foo.test.ts',
                'apps/generic/src/lib/foo.ts',
            )
        ]

    def test_astro_source_excluded_from_deletion_check(self, tmp_path):
        """`.astro` esta en FRONTEND_COVERAGE_EXCLUDES, no triggerea orphan."""
        from shared.deletion_mirror import collect_orphan_pairs

        # Aunque borremos el .astro, no debe contar como orphan
        _make_file(
            tmp_path,
            'apps/generic/tests/unit/components/Hero.test.ts',
        )

        deleted = _empty_module_map()
        deleted['generic'] = ['apps/generic/src/components/Hero.astro']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_tests'] == []


# ---------------------------------------------------------------------------
# collect_orphan_pairs - package
# ---------------------------------------------------------------------------


class TestCollectOrphanPairsPackage:
    """Detecta huerfanos en packages/<PKG>/."""

    def test_orphan_test_when_ts_source_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        _make_file(tmp_path, 'packages/content/tests/unit/schemas.test.ts')

        deleted = _empty_module_map()
        deleted['pkg-content'] = ['packages/content/src/schemas.ts']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_tests'] == [
            (
                'pkg-content',
                'packages/content/src/schemas.ts',
                'packages/content/tests/unit/schemas.test.ts',
            )
        ]

    def test_orphan_source_when_ts_test_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        _make_file(tmp_path, 'packages/content/src/schemas.ts')

        deleted = _empty_module_map()
        deleted['pkg-content'] = ['packages/content/tests/unit/schemas.test.ts']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert result['orphan_sources'] == [
            (
                'pkg-content',
                'packages/content/tests/unit/schemas.test.ts',
                'packages/content/src/schemas.ts',
            )
        ]


# ---------------------------------------------------------------------------
# collect_orphan_pairs - mixed scenarios
# ---------------------------------------------------------------------------


class TestCollectOrphanPairsMixed:
    """Casos combinados: empty inputs, multiples modulos, etc."""

    def test_empty_input_returns_empty_result(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        result = collect_orphan_pairs(
            _empty_module_map(),
            project_root=tmp_path,
        )

        assert result == {'orphan_tests': [], 'orphan_sources': []}

    def test_multiple_modules_in_single_changeset(self, tmp_path):
        """Server source + app test eliminados, ambos con contraparte en disco."""
        from shared.deletion_mirror import collect_orphan_pairs

        # Server source eliminado, test sigue en disco
        _make_file(tmp_path, 'server/tests/unit/src/apps/foo/bar.py')

        # App test eliminado, source sigue en disco
        _make_file(tmp_path, 'apps/generic/src/lib/foo.ts')

        deleted = _empty_module_map()
        deleted['server'] = ['server/apps/foo/bar.py']
        deleted['generic'] = ['apps/generic/tests/unit/lib/foo.test.ts']

        result = collect_orphan_pairs(deleted, project_root=tmp_path)

        assert (
            'server',
            'server/apps/foo/bar.py',
            'server/tests/unit/src/apps/foo/bar.py',
        ) in result['orphan_tests']
        assert (
            'generic',
            'apps/generic/tests/unit/lib/foo.test.ts',
            'apps/generic/src/lib/foo.ts',
        ) in result['orphan_sources']
