"""Unit tests for shared.purity.

find_forbidden_js_files(module, files, project_root) -> list[str]

Returns files that violate "TypeScript only" policy:
  - .js, .jsx, .mjs, .cjs forbidden inside apps/<APP>/ y packages/<PKG>/
  - Allowlist: <module-root>/{*.config,vitest.config,postcss.config}.{js,mjs,cjs}
  - node_modules/, dist/, .astro/, coverage/ paths ignored
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# find_forbidden_js_files - Astro app (representado por 'generic')
# ---------------------------------------------------------------------------


class TestFindForbiddenJsFilesApp:
    def test_js_file_in_app_src_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            ['apps/generic/src/utils/foo.js'],
            project_root=tmp_path,
        )

        assert result == ['apps/generic/src/utils/foo.js']

    def test_jsx_file_in_app_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            ['apps/generic/src/components/Foo.jsx'],
            project_root=tmp_path,
        )

        assert result == ['apps/generic/src/components/Foo.jsx']

    def test_mjs_in_subdir_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            ['apps/generic/src/utils/helper.mjs'],
            project_root=tmp_path,
        )

        assert result == ['apps/generic/src/utils/helper.mjs']

    def test_cjs_in_subdir_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            ['apps/generic/src/legacy.cjs'],
            project_root=tmp_path,
        )

        assert result == ['apps/generic/src/legacy.cjs']

    def test_ts_and_astro_files_are_allowed(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            [
                'apps/generic/src/utils/foo.ts',
                'apps/generic/src/components/Hero.astro',
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_config_js_at_root_is_allowed(self, tmp_path):
        """Configs `*.config.{js,mjs,cjs}` permitidos en module root."""
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            [
                'apps/generic/astro.config.mjs',
                'apps/generic/vitest.config.mjs',
                'apps/generic/postcss.config.cjs',
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_vitest_config_at_root_is_allowed(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            ['apps/generic/vitest.config.js'],
            project_root=tmp_path,
        )

        assert result == []

    def test_config_in_subdir_is_not_allowed(self, tmp_path):
        """Allowlist aplica solo al module root, no a subdirs."""
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            ['apps/generic/src/utils/my.config.js'],
            project_root=tmp_path,
        )

        assert result == ['apps/generic/src/utils/my.config.js']

    def test_node_modules_ignored(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            [
                'apps/generic/node_modules/lodash/index.js',
                'apps/generic/node_modules/foo/bar.jsx',
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_dist_and_astro_cache_ignored(self, tmp_path):
        """dist/ y .astro/ son excluidos."""
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            [
                'apps/generic/dist/bundle.js',
                'apps/generic/.astro/content.d.ts',
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_files_outside_module_are_skipped(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            [
                'server/manage.py',
                'packages/content/src/foo.ts',
                'apps/hub/src/x.js',  # otra app, no la pedida
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_multiple_violations_returned_in_order(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'generic',
            [
                'apps/generic/src/utils/a.js',
                'apps/generic/src/utils/b.ts',
                'apps/generic/src/c.jsx',
                'apps/generic/astro.config.mjs',  # allowed
            ],
            project_root=tmp_path,
        )

        assert result == [
            'apps/generic/src/utils/a.js',
            'apps/generic/src/c.jsx',
        ]


# ---------------------------------------------------------------------------
# find_forbidden_js_files - Package (representado por 'pkg-content')
# ---------------------------------------------------------------------------


class TestFindForbiddenJsFilesPackage:
    def test_js_in_package_src_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'pkg-content',
            ['packages/content/src/utils/foo.js'],
            project_root=tmp_path,
        )

        assert result == ['packages/content/src/utils/foo.js']

    def test_vitest_config_at_root_is_allowed(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'pkg-content',
            [
                'packages/content/vitest.config.mjs',
                'packages/content/postcss.config.cjs',
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_dist_in_package_ignored(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'pkg-content',
            ['packages/content/dist/index.js'],
            project_root=tmp_path,
        )

        assert result == []


# ---------------------------------------------------------------------------
# Invalid module
# ---------------------------------------------------------------------------


class TestFindForbiddenJsFilesInvalid:
    def test_unknown_module_raises(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        with pytest.raises(ValueError, match='module'):
            find_forbidden_js_files(
                'unknown',
                [],
                project_root=tmp_path,
            )
