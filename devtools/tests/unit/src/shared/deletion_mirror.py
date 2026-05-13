"""Unit tests for shared.deletion_mirror.

Path mirroring: devtools/shared/deletion_mirror.py -> this file.
"""

from pathlib import Path

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# classify_deleted_files
# ---------------------------------------------------------------------------


class TestClassifyDeletedFiles:
    """Clasifica una lista plana de paths eliminados por módulo."""

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
        assert result['dashboard'] == []
        assert result['landing'] == []

    def test_classifies_app_ts_and_vue(self):
        from shared.deletion_mirror import classify_deleted_files

        result = classify_deleted_files(
            [
                'dashboard/stores/useFoo.ts',
                'dashboard/app/components/DFCard.vue',
            ]
        )

        assert result['dashboard'] == [
            'dashboard/stores/useFoo.ts',
            'dashboard/app/components/DFCard.vue',
        ]
        assert result['server'] == []
        assert result['landing'] == []

    def test_classifies_landing_ts_and_astro(self):
        from shared.deletion_mirror import classify_deleted_files

        result = classify_deleted_files(
            [
                'landing/src/lib/foo.ts',
                'landing/src/components/Hero.astro',
            ]
        )

        assert result['landing'] == [
            'landing/src/lib/foo.ts',
            'landing/src/components/Hero.astro',
        ]
        assert result['server'] == []
        assert result['dashboard'] == []

    def test_ignores_non_relevant_extensions(self):
        from shared.deletion_mirror import classify_deleted_files

        result = classify_deleted_files(
            [
                'README.md',
                'docker/Dockerfile',
                'dashboard/package.json',
                'devtools/shared/foo.py',
            ]
        )

        assert result == {'server': [], 'dashboard': [], 'landing': []}


# ---------------------------------------------------------------------------
# collect_orphan_pairs - server
# ---------------------------------------------------------------------------


class TestCollectOrphanPairsServer:
    """Detecta huerfanos cuando solo se elimina un lado del par server."""

    def _make_file(self, root: Path, path: str) -> None:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('')

    def test_orphan_test_when_source_deleted_and_mirror_remains(
        self,
        tmp_path,
    ):
        from shared.deletion_mirror import collect_orphan_pairs

        # El test mirror sigue en disco, el source fue eliminado
        self._make_file(
            tmp_path,
            'server/tests/unit/src/apps/foo/services/bar.py',
        )

        result = collect_orphan_pairs(
            {
                'server': ['server/apps/foo/services/bar.py'],
                'dashboard': [],
                'landing': [],
            },
            project_root=tmp_path,
        )

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

        # El source sigue en disco, el test fue eliminado
        self._make_file(tmp_path, 'server/apps/foo/services/bar.py')

        result = collect_orphan_pairs(
            {
                'server': ['server/tests/unit/src/apps/foo/services/bar.py'],
                'dashboard': [],
                'landing': [],
            },
            project_root=tmp_path,
        )

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

        # Ningun archivo en disco, ambos eliminados
        result = collect_orphan_pairs(
            {
                'server': [
                    'server/apps/foo/services/bar.py',
                    'server/tests/unit/src/apps/foo/services/bar.py',
                ],
                'dashboard': [],
                'landing': [],
            },
            project_root=tmp_path,
        )

        assert result['orphan_tests'] == []
        assert result['orphan_sources'] == []

    def test_excluded_paths_do_not_trigger_orphan(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        # Eliminamos un __init__.py (excluido). No debe haber orphan ni siquiera
        # si su mirror existiera (lo cual es absurdo, pero verificamos exclusión).
        self._make_file(tmp_path, 'server/tests/unit/src/apps/foo/__init__.py')

        result = collect_orphan_pairs(
            {
                'server': ['server/apps/foo/__init__.py'],
                'dashboard': [],
                'landing': [],
            },
            project_root=tmp_path,
        )

        assert result['orphan_tests'] == []
        assert result['orphan_sources'] == []


# ---------------------------------------------------------------------------
# collect_orphan_pairs - app
# ---------------------------------------------------------------------------


class TestCollectOrphanPairsApp:
    """Detecta huerfanos en el módulo dashboard."""

    def _make_file(self, root: Path, path: str) -> None:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('')

    def test_orphan_test_when_ts_source_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        self._make_file(tmp_path, 'dashboard/tests/unit/src/stores/useFoo.ts')

        result = collect_orphan_pairs(
            {
                'server': [],
                'dashboard': ['dashboard/stores/useFoo.ts'],
                'landing': [],
            },
            project_root=tmp_path,
        )

        assert result['orphan_tests'] == [
            (
                'dashboard',
                'dashboard/stores/useFoo.ts',
                'dashboard/tests/unit/src/stores/useFoo.ts',
            )
        ]

    def test_orphan_source_when_ts_test_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        self._make_file(tmp_path, 'dashboard/stores/useFoo.ts')

        result = collect_orphan_pairs(
            {
                'server': [],
                'dashboard': ['dashboard/tests/unit/src/stores/useFoo.ts'],
                'landing': [],
            },
            project_root=tmp_path,
        )

        assert result['orphan_sources'] == [
            (
                'dashboard',
                'dashboard/tests/unit/src/stores/useFoo.ts',
                'dashboard/stores/useFoo.ts',
            )
        ]

    def test_vue_source_excluded_from_deletion_check(self, tmp_path):
        """Componentes .vue están excluidos de coverage, no deben triggerear orphan."""
        from shared.deletion_mirror import collect_orphan_pairs

        # Aunque borremos el .vue, no debe contar como orphan
        self._make_file(
            tmp_path,
            'dashboard/tests/unit/src/app/components/DFCard.ts',
        )

        result = collect_orphan_pairs(
            {
                'server': [],
                'dashboard': ['dashboard/app/components/DFCard.vue'],
                'landing': [],
            },
            project_root=tmp_path,
        )

        assert result['orphan_tests'] == []


# ---------------------------------------------------------------------------
# collect_orphan_pairs - landing
# ---------------------------------------------------------------------------


class TestCollectOrphanPairsLanding:
    """Detecta huerfanos en el módulo landing."""

    def _make_file(self, root: Path, path: str) -> None:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('')

    def test_orphan_test_when_ts_source_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        self._make_file(tmp_path, 'landing/tests/unit/src/lib/foo.ts')

        result = collect_orphan_pairs(
            {
                'server': [],
                'dashboard': [],
                'landing': ['landing/src/lib/foo.ts'],
            },
            project_root=tmp_path,
        )

        assert result['orphan_tests'] == [
            (
                'landing',
                'landing/src/lib/foo.ts',
                'landing/tests/unit/src/lib/foo.ts',
            )
        ]

    def test_orphan_source_when_ts_test_deleted(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        self._make_file(tmp_path, 'landing/src/lib/foo.ts')

        result = collect_orphan_pairs(
            {
                'server': [],
                'dashboard': [],
                'landing': ['landing/tests/unit/src/lib/foo.ts'],
            },
            project_root=tmp_path,
        )

        assert result['orphan_sources'] == [
            (
                'landing',
                'landing/tests/unit/src/lib/foo.ts',
                'landing/src/lib/foo.ts',
            )
        ]

    def test_astro_source_excluded(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        self._make_file(
            tmp_path,
            'landing/tests/unit/src/components/Hero.ts',
        )

        result = collect_orphan_pairs(
            {
                'server': [],
                'dashboard': [],
                'landing': ['landing/src/components/Hero.astro'],
            },
            project_root=tmp_path,
        )

        assert result['orphan_tests'] == []


# ---------------------------------------------------------------------------
# collect_orphan_pairs - mixed scenarios
# ---------------------------------------------------------------------------


class TestCollectOrphanPairsMixed:
    """Casos combinados: empty inputs, multiples módulos, etc."""

    def test_empty_input_returns_empty_result(self, tmp_path):
        from shared.deletion_mirror import collect_orphan_pairs

        result = collect_orphan_pairs(
            {'server': [], 'dashboard': [], 'landing': []},
            project_root=tmp_path,
        )

        assert result == {'orphan_tests': [], 'orphan_sources': []}

    def test_multiple_modules_in_single_changeset(self, tmp_path):
        """Server source y app test eliminados, ambos con contraparte en disco."""
        from shared.deletion_mirror import collect_orphan_pairs

        # Server source eliminado, test sigue en disco
        (tmp_path / 'server' / 'tests' / 'unit' / 'src' / 'apps' / 'foo').mkdir(
            parents=True,
        )
        (
            tmp_path
            / 'server'
            / 'tests'
            / 'unit'
            / 'src'
            / 'apps'
            / 'foo'
            / 'bar.py'
        ).write_text('')

        # App test eliminado, source sigue en disco
        (tmp_path / 'dashboard' / 'stores').mkdir(parents=True)
        (tmp_path / 'dashboard' / 'stores' / 'useFoo.ts').write_text('')

        result = collect_orphan_pairs(
            {
                'server': ['server/apps/foo/bar.py'],
                'dashboard': ['dashboard/tests/unit/src/stores/useFoo.ts'],
                'landing': [],
            },
            project_root=tmp_path,
        )

        assert (
            'server',
            'server/apps/foo/bar.py',
            'server/tests/unit/src/apps/foo/bar.py',
        ) in result['orphan_tests']
        assert (
            'dashboard',
            'dashboard/tests/unit/src/stores/useFoo.ts',
            'dashboard/stores/useFoo.ts',
        ) in result['orphan_sources']
