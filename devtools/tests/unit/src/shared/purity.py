"""Unit tests for shared.purity.

find_forbidden_js_files(module, files, project_root) -> list[str]

Returns files that violate "TypeScript only" policy:
  - .js, .jsx, .mjs, .cjs are forbidden inside <module>/
  - Allowlist: <module>/{*.config,vitest.config}.{js,mjs,cjs} at module root
  - node_modules/ and dist/ paths are ignored
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# find_forbidden_js_files
# ---------------------------------------------------------------------------


class TestFindForbiddenJsFilesDashboard:
    def test_js_file_in_dashboard_root_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/app/utils/foo.js'],
            project_root=tmp_path,
        )

        assert result == ['dashboard/app/utils/foo.js']

    def test_jsx_file_in_dashboard_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/app/components/Foo.jsx'],
            project_root=tmp_path,
        )

        assert result == ['dashboard/app/components/Foo.jsx']

    def test_mjs_in_subdir_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/app/utils/helper.mjs'],
            project_root=tmp_path,
        )

        assert result == ['dashboard/app/utils/helper.mjs']

    def test_cjs_in_subdir_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/stores/legacy.cjs'],
            project_root=tmp_path,
        )

        assert result == ['dashboard/stores/legacy.cjs']

    def test_ts_files_are_allowed(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/app/utils/foo.ts', 'dashboard/app/components/Foo.vue'],
            project_root=tmp_path,
        )

        assert result == []

    def test_config_js_at_root_is_allowed(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            [
                'dashboard/next.config.js',
                'dashboard/vitest.config.mjs',
                'dashboard/postcss.config.cjs',
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_vitest_config_at_root_is_allowed(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/vitest.config.js'],
            project_root=tmp_path,
        )

        assert result == []

    def test_config_in_subdir_is_not_allowed(self, tmp_path):
        """Allowlist applies only at module root."""
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/app/utils/my.config.js'],
            project_root=tmp_path,
        )

        assert result == ['dashboard/app/utils/my.config.js']

    def test_node_modules_ignored(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            [
                'dashboard/node_modules/lodash/index.js',
                'dashboard/node_modules/foo/bar.jsx',
            ],
            project_root=tmp_path,
        )

        assert result == []

    def test_dist_ignored(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['dashboard/dist/bundle.js', 'dashboard/.next/server/output.js'],
            project_root=tmp_path,
        )

        assert result == []

    def test_files_outside_module_are_skipped(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            ['server/manage.py', 'landing/src/foo.ts'],
            project_root=tmp_path,
        )

        assert result == []

    def test_multiple_violations_returned_in_order(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'dashboard',
            [
                'dashboard/app/utils/a.js',
                'dashboard/app/utils/b.ts',
                'dashboard/stores/c.jsx',
                'dashboard/next.config.js',  # allowed
            ],
            project_root=tmp_path,
        )

        assert result == ['dashboard/app/utils/a.js', 'dashboard/stores/c.jsx']


class TestFindForbiddenJsFilesLanding:
    def test_js_in_landing_src_is_forbidden(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'landing',
            ['landing/src/utils/foo.js'],
            project_root=tmp_path,
        )

        assert result == ['landing/src/utils/foo.js']

    def test_astro_config_at_root_is_allowed(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'landing',
            ['landing/astro.config.mjs', 'landing/vitest.config.mjs'],
            project_root=tmp_path,
        )

        assert result == []

    def test_dist_in_landing_ignored(self, tmp_path):
        from shared.purity import find_forbidden_js_files

        result = find_forbidden_js_files(
            'landing',
            ['landing/dist/index.js'],
            project_root=tmp_path,
        )

        assert result == []
