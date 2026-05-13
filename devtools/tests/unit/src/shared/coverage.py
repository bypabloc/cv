"""Unit tests for shared.coverage frontend verifier."""

import json

import pytest


pytestmark = pytest.mark.unit


def _write_summary(path, files: dict) -> None:
    payload = {'total': {'lines': {'pct': 0}}, **files}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


# ---------------------------------------------------------------------------
# verify_frontend_coverage - dashboard module
# ---------------------------------------------------------------------------


class TestVerifyFrontendCoverageDashboard:
    def test_file_above_threshold_is_passed(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = tmp_path / 'dashboard' / 'coverage' / 'coverage-summary.json'
        abs_source = str(tmp_path / 'dashboard' / 'lib' / 'foo.ts')
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 95.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'dashboard',
            [
                (
                    'dashboard/lib/foo.ts',
                    'dashboard/tests/unit/src/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert len(passed) == 1
        assert passed[0]['source'] == 'dashboard/lib/foo.ts'
        assert passed[0]['pct'] == 95.0
        assert passed[0]['status'] == 'OK'
        assert failed == []

    def test_file_below_threshold_is_failed(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = tmp_path / 'dashboard' / 'coverage' / 'coverage-summary.json'
        abs_source = str(tmp_path / 'dashboard' / 'lib' / 'foo.ts')
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 50.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'dashboard',
            [
                (
                    'dashboard/lib/foo.ts',
                    'dashboard/tests/unit/src/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert passed == []
        assert len(failed) == 1
        assert failed[0]['source'] == 'dashboard/lib/foo.ts'
        assert failed[0]['pct'] == 50.0
        assert failed[0]['status'] == 'FAIL'

    def test_custom_threshold(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = tmp_path / 'dashboard' / 'coverage' / 'coverage-summary.json'
        abs_source = str(tmp_path / 'dashboard' / 'lib' / 'foo.ts')
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 75.0}},
            },
        )

        passed, _ = verify_frontend_coverage(
            'dashboard',
            [
                (
                    'dashboard/lib/foo.ts',
                    'dashboard/tests/unit/src/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
            threshold=70,
        )

        assert len(passed) == 1
        assert passed[0]['status'] == 'OK'

    def test_file_not_in_summary_is_skipped(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = tmp_path / 'dashboard' / 'coverage' / 'coverage-summary.json'
        _write_summary(summary, {})

        passed, failed = verify_frontend_coverage(
            'dashboard',
            [
                (
                    'dashboard/lib/missing.ts',
                    'dashboard/tests/unit/src/lib/missing.test.ts',
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
            'dashboard',
            [
                (
                    'dashboard/lib/foo.ts',
                    'dashboard/tests/unit/src/lib/foo.test.ts',
                )
            ],
            project_root=tmp_path,
        )

        assert passed == []
        assert len(failed) == 1
        assert failed[0]['status'] == 'MISSING'

    def test_vue_source_marked_excluded(self, tmp_path):
        """`.vue` files marcados como EXCLUDED del coverage 80%.

        verify_frontend_coverage detecta .vue via is_excluded_from_coverage
        y los reporta con status 'EXCLUDED' (passed) sin verificar pct.
        """
        from shared.coverage import verify_frontend_coverage

        summary = tmp_path / 'dashboard' / 'coverage' / 'coverage-summary.json'
        abs_source = str(
            tmp_path / 'dashboard' / 'app' / 'components' / 'Foo.vue'
        )
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 30.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'dashboard',
            [
                (
                    'dashboard/app/components/Foo.vue',
                    'dashboard/tests/unit/src/app/components/Foo.ts',
                )
            ],
            project_root=tmp_path,
        )

        # Excluido aun con pct=30 (por debajo del umbral)
        assert len(passed) == 1
        assert passed[0]['status'] == 'EXCLUDED'
        assert failed == []


# ---------------------------------------------------------------------------
# verify_frontend_coverage - landing module
# ---------------------------------------------------------------------------


class TestVerifyFrontendCoverageLanding:
    def test_landing_uses_landing_coverage_dir(self, tmp_path):
        from shared.coverage import verify_frontend_coverage

        summary = tmp_path / 'landing' / 'coverage' / 'coverage-summary.json'
        abs_source = str(tmp_path / 'landing' / 'src' / 'utils' / 'bar.ts')
        _write_summary(
            summary,
            {
                abs_source: {'lines': {'pct': 88.0}},
            },
        )

        passed, failed = verify_frontend_coverage(
            'landing',
            [
                (
                    'landing/src/utils/bar.ts',
                    'landing/tests/unit/src/utils/bar.ts',
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
