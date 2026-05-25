"""Unit tests for shared.coverage frontend verifier.

Portfolio frontend modulos:
- Apps Astro: 'hub'/'generic'/etc. summary en apps/<APP>/coverage/coverage-summary.json
- Packages:   'pkg-<X>' summary en packages/<X>/coverage/coverage-summary.json
"""

import json

import pytest


pytestmark = pytest.mark.unit


def _write_summary(path, files: dict) -> None:
    payload = {'total': {'lines': {'pct': 0}}, **files}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


# ---------------------------------------------------------------------------
# verify_frontend_coverage - Astro app (representado por 'generic')
# ---------------------------------------------------------------------------


class TestVerifyFrontendCoverageApp:
    def test_file_above_threshold_is_passed(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = (
            tmp_path / 'apps' / 'generic' / 'coverage' / 'coverage-summary.json'
        )
        abs_source = str(
            tmp_path / 'apps' / 'generic' / 'src' / 'lib' / 'foo.ts'
        )
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 95.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'generic',
            [
                (
                    'apps/generic/src/lib/foo.ts',
                    'apps/generic/tests/unit/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert len(passed) == 1
        assert passed[0]['source'] == 'apps/generic/src/lib/foo.ts'
        assert passed[0]['pct'] == 95.0
        assert passed[0]['status'] == 'OK'
        assert failed == []

    def test_file_below_threshold_is_failed(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = (
            tmp_path / 'apps' / 'generic' / 'coverage' / 'coverage-summary.json'
        )
        abs_source = str(
            tmp_path / 'apps' / 'generic' / 'src' / 'lib' / 'foo.ts'
        )
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 50.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'generic',
            [
                (
                    'apps/generic/src/lib/foo.ts',
                    'apps/generic/tests/unit/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert passed == []
        assert len(failed) == 1
        assert failed[0]['source'] == 'apps/generic/src/lib/foo.ts'
        assert failed[0]['pct'] == 50.0
        assert failed[0]['status'] == 'FAIL'

    def test_custom_threshold(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = (
            tmp_path / 'apps' / 'generic' / 'coverage' / 'coverage-summary.json'
        )
        abs_source = str(
            tmp_path / 'apps' / 'generic' / 'src' / 'lib' / 'foo.ts'
        )
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 75.0}},
            },
        )

        passed, _ = verify_frontend_coverage(
            'generic',
            [
                (
                    'apps/generic/src/lib/foo.ts',
                    'apps/generic/tests/unit/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
            threshold=70,
        )

        assert len(passed) == 1
        assert passed[0]['status'] == 'OK'

    def test_file_not_in_summary_is_skipped(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = (
            tmp_path / 'apps' / 'generic' / 'coverage' / 'coverage-summary.json'
        )
        _write_summary(summary, {})

        passed, failed = verify_frontend_coverage(
            'generic',
            [
                (
                    'apps/generic/src/lib/missing.ts',
                    'apps/generic/tests/unit/lib/missing.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert len(passed) == 1
        assert passed[0]['status'] == 'SKIP'
        assert passed[0]['pct'] is None
        assert failed == []

    def test_missing_summary_file_returns_failure(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        passed, failed = verify_frontend_coverage(
            'generic',
            [
                (
                    'apps/generic/src/lib/foo.ts',
                    'apps/generic/tests/unit/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert passed == []
        assert len(failed) == 1
        assert failed[0]['status'] == 'MISSING'

    def test_astro_source_marked_excluded(self, tmp_path):
        """`.astro` files marcados como EXCLUDED del coverage 80%.

        verify_frontend_coverage detecta '.astro' via
        is_excluded_from_coverage y los reporta con status 'EXCLUDED'
        (passed) sin verificar pct.
        """
        from shared.coverage import verify_frontend_coverage

        summary = (
            tmp_path / 'apps' / 'generic' / 'coverage' / 'coverage-summary.json'
        )
        abs_source = str(
            tmp_path / 'apps' / 'generic' / 'src' / 'components' / 'Hero.astro'
        )
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 30.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'generic',
            [
                (
                    'apps/generic/src/components/Hero.astro',
                    'apps/generic/tests/unit/components/Hero.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        # Excluido aun con pct=30 (por debajo del umbral)
        assert len(passed) == 1
        assert passed[0]['status'] == 'EXCLUDED'
        assert failed == []


# ---------------------------------------------------------------------------
# verify_frontend_coverage - Package (representado por 'pkg-content')
# ---------------------------------------------------------------------------


class TestVerifyFrontendCoveragePackage:
    def test_package_uses_packages_coverage_dir(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = (
            tmp_path
            / 'packages'
            / 'content'
            / 'coverage'
            / 'coverage-summary.json'
        )
        abs_source = str(
            tmp_path / 'packages' / 'content' / 'src' / 'schemas.ts'
        )
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 88.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'pkg-content',
            [
                (
                    'packages/content/src/schemas.ts',
                    'packages/content/tests/unit/schemas.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert len(passed) == 1
        assert passed[0]['pct'] == 88.0
        assert failed == []


# ---------------------------------------------------------------------------
# Invalid module
# ---------------------------------------------------------------------------


class TestVerifyFrontendCoverageInvalid:
    def test_unknown_module_raises(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        with pytest.raises(ValueError, match='module'):
            verify_frontend_coverage(
                'unknown',
                [],
                project_root=tmp_path,
            )
