"""Unit tests for shared.classification frontend classifier.

Path mirroring: devtools/shared/classification.py -> this file.
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# classify_frontend_files - dashboard module
# ---------------------------------------------------------------------------


class TestClassifyFrontendFilesDashboard:
    """Mirror dashboard/<X> -> dashboard/tests/unit/src/<X>."""

    def test_source_with_existing_mirror_returns_pair(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'lib').mkdir(parents=True)
        (tmp_path / 'dashboard' / 'lib' / 'foo.ts').write_text('')
        (tmp_path / 'dashboard' / 'tests' / 'unit' / 'src' / 'lib').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'lib'
            / 'foo.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/lib/foo.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == [
            (
                'dashboard/lib/foo.ts',
                'dashboard/tests/unit/src/lib/foo.test.ts',
            ),
        ]
        assert result['missing_mirrors'] == []
        assert result['run_coverage'] is True

    def test_shadcn_ui_source_is_excluded(self, tmp_path):
        """`components/ui/` (shadcn copy-paste) excluido del coverage 80%.

        Razon: shadcn/ui son componentes copy-paste verbatim del registry,
        no se modifican con logica de negocio. Logica testeable vive en
        components/features/ y modules/.
        """
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'components' / 'ui').mkdir(parents=True)
        (
            tmp_path / 'dashboard' / 'components' / 'ui' / 'button.tsx'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/components/ui/button.tsx'],
            project_root=tmp_path,
        )

        # components/ui/ excluido: no aparece en pairs ni en missing_mirrors
        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_stores_root_is_supported(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'stores').mkdir(parents=True)
        (tmp_path / 'dashboard' / 'stores' / 'use-auth.ts').write_text('')
        (tmp_path / 'dashboard' / 'tests' / 'unit' / 'src' / 'stores').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'stores'
            / 'use-auth.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/stores/use-auth.ts'],
            project_root=tmp_path,
        )

        assert (
            'dashboard/stores/use-auth.ts',
            'dashboard/tests/unit/src/stores/use-auth.test.ts',
        ) in result['unit_pairs']

    def test_lib_root_is_supported(self, tmp_path):
        """Sources en dashboard/lib/ tambien tienen mirror obligatorio."""
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'lib' / 'validators').mkdir(parents=True)
        (tmp_path / 'dashboard' / 'lib' / 'validators' / 'rut.ts').write_text(
            ''
        )
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'lib'
            / 'validators'
        ).mkdir(parents=True)
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'lib'
            / 'validators'
            / 'rut.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/lib/validators/rut.ts'],
            project_root=tmp_path,
        )

        assert (
            'dashboard/lib/validators/rut.ts',
            'dashboard/tests/unit/src/lib/validators/rut.test.ts',
        ) in result['unit_pairs']

    def test_tsx_source_pairs_with_test_ts(self, tmp_path):
        """`.tsx` source mapea a `.test.ts` en mirror (siempre).

        Usa `dashboard/modules/items/schemas/` (logica testeable Zod, NO
        excluido) en lugar de actions/api/store que estan excluidos por
        ser wrappers thin testeados via E2E.
        """
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'modules' / 'items' / 'schemas').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'dashboard'
            / 'modules'
            / 'items'
            / 'schemas'
            / 'item.tsx'
        ).write_text('')
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'modules'
            / 'items'
            / 'schemas'
        ).mkdir(parents=True)
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'modules'
            / 'items'
            / 'schemas'
            / 'item.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/modules/items/schemas/item.tsx'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == [
            (
                'dashboard/modules/items/schemas/item.tsx',
                'dashboard/tests/unit/src/modules/items/schemas/item.test.ts',
            ),
        ]

    def test_source_without_mirror_is_missing(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'lib').mkdir(parents=True)
        (tmp_path / 'dashboard' / 'lib' / 'orphan.ts').write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/lib/orphan.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == [
            (
                'dashboard/lib/orphan.ts',
                'dashboard/tests/unit/src/lib/orphan.test.ts',
            ),
        ]
        assert result['run_coverage'] is False

    def test_test_file_orphan_pairs_with_existing_source(self, tmp_path):
        """A staged test file pairs back to its source if the source exists."""
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'lib').mkdir(parents=True)
        (tmp_path / 'dashboard' / 'lib' / 'foo.ts').write_text('')
        (tmp_path / 'dashboard' / 'tests' / 'unit' / 'src' / 'lib').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'lib'
            / 'foo.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/tests/unit/src/lib/foo.test.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == [
            (
                'dashboard/lib/foo.ts',
                'dashboard/tests/unit/src/lib/foo.test.ts',
            ),
        ]

    def test_files_under_tests_are_not_treated_as_source(self, tmp_path):
        """Tests under tests/ never become source candidates."""
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'tests' / 'unit' / 'src').mkdir(parents=True)
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'isolated.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/tests/unit/src/isolated.test.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_node_modules_files_are_excluded(self, tmp_path):
        from shared.classification import classify_frontend_files

        result = classify_frontend_files(
            'dashboard',
            ['dashboard/node_modules/pkg/index.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_dedupe_when_source_and_test_both_staged(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'dashboard' / 'lib').mkdir(parents=True)
        (tmp_path / 'dashboard' / 'lib' / 'foo.ts').write_text('')
        (tmp_path / 'dashboard' / 'tests' / 'unit' / 'src' / 'lib').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'dashboard'
            / 'tests'
            / 'unit'
            / 'src'
            / 'lib'
            / 'foo.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'dashboard',
            [
                'dashboard/lib/foo.ts',
                'dashboard/tests/unit/src/lib/foo.test.ts',
            ],
            project_root=tmp_path,
        )

        assert len(result['unit_pairs']) == 1


# ---------------------------------------------------------------------------
# classify_frontend_files - landing module
# ---------------------------------------------------------------------------


class TestClassifyFrontendFilesLanding:
    """Mirror landing/src/<X> -> landing/tests/unit/src/<X>."""

    def test_source_with_existing_mirror_returns_pair(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'landing' / 'src' / 'utils').mkdir(parents=True)
        (tmp_path / 'landing' / 'src' / 'utils' / 'bar.ts').write_text('')
        (tmp_path / 'landing' / 'tests' / 'unit' / 'src' / 'utils').mkdir(
            parents=True
        )
        (
            tmp_path / 'landing' / 'tests' / 'unit' / 'src' / 'utils' / 'bar.ts'
        ).write_text('')

        result = classify_frontend_files(
            'landing',
            ['landing/src/utils/bar.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == [
            ('landing/src/utils/bar.ts', 'landing/tests/unit/src/utils/bar.ts'),
        ]
        assert result['run_coverage'] is True

    def test_astro_source_excluded_from_coverage(self, tmp_path):
        """`.astro` files (Astro components/pages) excluidos del coverage 80%.

        Razon: Astro es template-only, no business logic. /pages/ es
        file-based routing testeado via E2E specs.
        """
        from shared.classification import classify_frontend_files

        (tmp_path / 'landing' / 'src' / 'pages').mkdir(parents=True)
        (tmp_path / 'landing' / 'src' / 'pages' / 'about.astro').write_text('')

        result = classify_frontend_files(
            'landing',
            ['landing/src/pages/about.astro'],
            project_root=tmp_path,
        )

        # .astro y /pages/ excluidos: no exigen mirror
        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_source_without_mirror_is_missing(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'landing' / 'src' / 'utils').mkdir(parents=True)
        (tmp_path / 'landing' / 'src' / 'utils' / 'orphan.ts').write_text('')

        result = classify_frontend_files(
            'landing',
            ['landing/src/utils/orphan.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == [
            (
                'landing/src/utils/orphan.ts',
                'landing/tests/unit/src/utils/orphan.ts',
            ),
        ]
        assert result['run_coverage'] is False

    def test_files_outside_src_are_ignored(self, tmp_path):
        """Config files like landing/astro.config.mjs are not source candidates."""
        from shared.classification import classify_frontend_files

        result = classify_frontend_files(
            'landing',
            ['landing/astro.config.mjs', 'landing/package.json'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []


# ---------------------------------------------------------------------------
# classify_frontend_files - invalid module
# ---------------------------------------------------------------------------


class TestClassifyFrontendFilesInvalid:
    def test_unknown_module_raises(self, tmp_path):
        from shared.classification import classify_frontend_files

        with pytest.raises(ValueError, match='module'):
            classify_frontend_files(
                'unknown',
                [],
                project_root=tmp_path,
            )
