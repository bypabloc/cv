"""Unit tests for shared.classification frontend classifier.

Path mirroring: devtools/shared/classification.py -> este archivo.

Portfolio modulos:
- Apps Astro: 'hub', 'generic', 'fintech', 'architect', 'leader', 'vibe'
  -> source: apps/<APP>/src/<X>.{ts,astro}
  -> test:   apps/<APP>/tests/unit/<X>.test.ts
- Packages:  'pkg-app-shared', 'pkg-content', 'pkg-cv-pdf', 'pkg-seo', 'pkg-ui'
  -> source: packages/<PKG>/src/<X>.ts
  -> test:   packages/<PKG>/tests/unit/<X>.test.ts
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# classify_frontend_files — Astro app (representada por 'generic')
# ---------------------------------------------------------------------------


class TestClassifyFrontendFilesApp:
    """Mirror apps/<APP>/src/<X> -> apps/<APP>/tests/unit/<X>."""

    def test_ts_source_with_existing_mirror_returns_pair(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'apps' / 'generic' / 'src' / 'lib').mkdir(parents=True)
        (tmp_path / 'apps' / 'generic' / 'src' / 'lib' / 'foo.ts').write_text(
            ''
        )
        (tmp_path / 'apps' / 'generic' / 'tests' / 'unit' / 'lib').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'apps'
            / 'generic'
            / 'tests'
            / 'unit'
            / 'lib'
            / 'foo.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'generic',
            ['apps/generic/src/lib/foo.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == [
            (
                'apps/generic/src/lib/foo.ts',
                'apps/generic/tests/unit/lib/foo.test.ts',
            ),
        ]
        assert result['missing_mirrors'] == []
        assert result['run_coverage'] is True

    def test_astro_source_excluded_from_coverage(self, tmp_path):
        """`.astro` excluido del coverage 80% (template-only, testeado E2E).

        FRONTEND_COVERAGE_EXCLUDES contiene '.astro', asi que un source
        .astro NO aparece en pairs ni en missing_mirrors —
        is_excluded_from_coverage corta la clasificacion.
        """
        from shared.classification import classify_frontend_files

        (tmp_path / 'apps' / 'generic' / 'src' / 'components').mkdir(
            parents=True
        )
        (
            tmp_path / 'apps' / 'generic' / 'src' / 'components' / 'Hero.astro'
        ).write_text('')

        result = classify_frontend_files(
            'generic',
            ['apps/generic/src/components/Hero.astro'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_source_without_mirror_is_missing(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'apps' / 'generic' / 'src' / 'lib').mkdir(parents=True)
        (
            tmp_path / 'apps' / 'generic' / 'src' / 'lib' / 'orphan.ts'
        ).write_text('')

        result = classify_frontend_files(
            'generic',
            ['apps/generic/src/lib/orphan.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == [
            (
                'apps/generic/src/lib/orphan.ts',
                'apps/generic/tests/unit/lib/orphan.test.ts',
            ),
        ]
        assert result['run_coverage'] is False

    def test_test_file_orphan_pairs_with_existing_source(self, tmp_path):
        """A staged test file pairs back to its source if the source exists."""
        from shared.classification import classify_frontend_files

        (tmp_path / 'apps' / 'generic' / 'src' / 'lib').mkdir(parents=True)
        (tmp_path / 'apps' / 'generic' / 'src' / 'lib' / 'foo.ts').write_text(
            ''
        )
        (tmp_path / 'apps' / 'generic' / 'tests' / 'unit' / 'lib').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'apps'
            / 'generic'
            / 'tests'
            / 'unit'
            / 'lib'
            / 'foo.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'generic',
            ['apps/generic/tests/unit/lib/foo.test.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == [
            (
                'apps/generic/src/lib/foo.ts',
                'apps/generic/tests/unit/lib/foo.test.ts',
            ),
        ]

    def test_files_under_tests_are_not_treated_as_source(self, tmp_path):
        """Archivos bajo tests/ nunca son source candidates."""
        from shared.classification import classify_frontend_files

        (tmp_path / 'apps' / 'generic' / 'tests' / 'unit').mkdir(parents=True)
        (
            tmp_path
            / 'apps'
            / 'generic'
            / 'tests'
            / 'unit'
            / 'isolated.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'generic',
            ['apps/generic/tests/unit/isolated.test.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_node_modules_files_are_excluded(self, tmp_path):
        from shared.classification import classify_frontend_files

        result = classify_frontend_files(
            'generic',
            ['apps/generic/node_modules/pkg/index.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_astro_build_dir_excluded(self, tmp_path):
        """Archivos bajo .astro/ (cache de build) se ignoran."""
        from shared.classification import classify_frontend_files

        result = classify_frontend_files(
            'generic',
            ['apps/generic/.astro/content.d.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_dedupe_when_source_and_test_both_staged(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'apps' / 'generic' / 'src' / 'lib').mkdir(parents=True)
        (tmp_path / 'apps' / 'generic' / 'src' / 'lib' / 'foo.ts').write_text(
            ''
        )
        (tmp_path / 'apps' / 'generic' / 'tests' / 'unit' / 'lib').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'apps'
            / 'generic'
            / 'tests'
            / 'unit'
            / 'lib'
            / 'foo.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'generic',
            [
                'apps/generic/src/lib/foo.ts',
                'apps/generic/tests/unit/lib/foo.test.ts',
            ],
            project_root=tmp_path,
        )

        assert len(result['unit_pairs']) == 1


# ---------------------------------------------------------------------------
# classify_frontend_files — Package (representado por 'pkg-content')
# ---------------------------------------------------------------------------


class TestClassifyFrontendFilesPackage:
    """Mirror packages/<PKG>/src/<X> -> packages/<PKG>/tests/unit/<X>."""

    def test_ts_source_with_existing_mirror_returns_pair(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'packages' / 'content' / 'src').mkdir(parents=True)
        (tmp_path / 'packages' / 'content' / 'src' / 'schemas.ts').write_text(
            ''
        )
        (tmp_path / 'packages' / 'content' / 'tests' / 'unit').mkdir(
            parents=True
        )
        (
            tmp_path
            / 'packages'
            / 'content'
            / 'tests'
            / 'unit'
            / 'schemas.test.ts'
        ).write_text('')

        result = classify_frontend_files(
            'pkg-content',
            ['packages/content/src/schemas.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == [
            (
                'packages/content/src/schemas.ts',
                'packages/content/tests/unit/schemas.test.ts',
            ),
        ]
        assert result['run_coverage'] is True

    def test_astro_is_not_a_package_source_extension(self, tmp_path):
        """Packages no aceptan .astro como source (solo .ts)."""
        from shared.classification import classify_frontend_files

        result = classify_frontend_files(
            'pkg-content',
            ['packages/content/src/Foo.astro'],
            project_root=tmp_path,
        )

        # .astro no es source_extension valida para packages -> nada para reportar
        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == []

    def test_source_without_mirror_is_missing(self, tmp_path):
        from shared.classification import classify_frontend_files

        (tmp_path / 'packages' / 'content' / 'src').mkdir(parents=True)
        (tmp_path / 'packages' / 'content' / 'src' / 'orphan.ts').write_text('')

        result = classify_frontend_files(
            'pkg-content',
            ['packages/content/src/orphan.ts'],
            project_root=tmp_path,
        )

        assert result['unit_pairs'] == []
        assert result['missing_mirrors'] == [
            (
                'packages/content/src/orphan.ts',
                'packages/content/tests/unit/orphan.test.ts',
            ),
        ]
        assert result['run_coverage'] is False

    def test_files_outside_src_are_ignored(self, tmp_path):
        """Files outside packages/<PKG>/src/ son ignorados."""
        from shared.classification import classify_frontend_files

        result = classify_frontend_files(
            'pkg-content',
            [
                'packages/content/package.json',
                'packages/content/vitest.config.ts',
            ],
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
