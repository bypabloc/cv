"""Unit tests for ai_audit.tools.lighthouse_psi.

Path mirroring: devtools/ai_audit/tools/lighthouse_psi.py -> este archivo.

`scrape()` requiere red — los tests cubren:
  - parse_payload (pure): parsing del JSON de PSI v5
  - get_api_key: extraccion de PSI_API_KEY desde docker/env/dev-cli/.{env}
                  via grep (sin volcar el .env completo)
"""

import os
from pathlib import Path

import pytest

from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.lighthouse_psi import LighthousePsi


pytestmark = pytest.mark.unit


def _payload(
    *,
    performance: float | None = 0.85,
    seo: float | None = 0.92,
    accessibility: float | None = 1.0,
    best_practices: float | None = 0.78,
    audits: dict | None = None,
) -> dict:
    """Helper: arma un payload PSI v5 minimo con scores configurables."""

    def cat(score: float | None, refs: list[dict]) -> dict:
        return {
            'score': score,
            'auditRefs': refs,
        }

    return {
        'lighthouseResult': {
            'categories': {
                'performance': cat(
                    performance,
                    [
                        {'id': 'lcp', 'weight': 10.0},
                        {'id': 'fcp', 'weight': 5.0},
                        {'id': 'inp', 'weight': 1.0},
                    ],
                ),
                'seo': cat(
                    seo,
                    [{'id': 'meta-description', 'weight': 3.0}],
                ),
                'accessibility': cat(
                    accessibility,
                    [{'id': 'color-contrast', 'weight': 7.0}],
                ),
                'best-practices': cat(
                    best_practices,
                    [{'id': 'no-document-write', 'weight': 1.0}],
                ),
            },
            'audits': audits
            or {
                'lcp': {
                    'title': 'LCP slow',
                    'description': 'Largest contentful paint > 2.5s',
                    'score': 0.3,
                },
                'fcp': {
                    'title': 'FCP slow',
                    'description': 'First contentful paint slow',
                    'score': 0.5,
                },
                'meta-description': {
                    'title': 'Document does not have a meta description',
                    'description': 'Add a meta description tag',
                    'score': 0,
                },
                'color-contrast': {
                    'title': 'Contrast OK',
                    'description': '',
                    'score': 1.0,
                },
            },
        }
    }


class TestParsePayload:
    """Pure parser del JSON de PSI v5."""

    def test_score_is_average_of_categories(self) -> None:
        """
        Given payload con performance=85, seo=92, a11y=100, bp=78,
        When parse_payload,
        Then score = round((85+92+100+78)/4) = 89.
        """
        tool = LighthousePsi()
        payload = _payload()

        result = tool.parse_payload(payload, 'https://x.com')

        assert result.score == 89

    def test_status_ok_and_tool_name(self) -> None:
        """Given payload valido, Then status=OK + tool='lighthouse_psi'."""
        tool = LighthousePsi()
        payload = _payload()

        result = tool.parse_payload(payload, 'https://x.com')

        assert result.status == Status.OK
        assert result.tool == 'lighthouse_psi'

    def test_categories_one_per_psi_category(self) -> None:
        """Given payload, Then categories tiene las 4 keys con scores 0-100."""
        tool = LighthousePsi()
        payload = _payload()

        result = tool.parse_payload(payload, 'https://x.com')

        assert result.categories['performance'] == 85
        assert result.categories['seo'] == 92
        assert result.categories['accessibility'] == 100
        assert result.categories['best-practices'] == 78

    def test_missing_category_is_na(self) -> None:
        """Given payload con seo=None, Then categories['seo'] == 'n/a'."""
        tool = LighthousePsi()
        payload = _payload(seo=None)

        result = tool.parse_payload(payload, 'https://x.com')

        assert result.categories['seo'] == 'n/a'

    def test_fixes_top_5_ordered_by_weight_desc(self) -> None:
        """
        Given audits con weights 10/5/1/7 y todos failing,
        When parse_payload,
        Then fixes ordenados por weight DESC.
        """
        tool = LighthousePsi()
        audits = {
            'lcp': {'title': 'LCP', 'score': 0.3},  # weight 10
            'fcp': {'title': 'FCP', 'score': 0.5},  # weight 5
            'inp': {'title': 'INP', 'score': 0.4},  # weight 1
            'color-contrast': {'title': 'Contrast', 'score': 0.6},  # weight 7
            'meta-description': {'title': 'Meta', 'score': 0},  # weight 3
        }
        payload = _payload(audits=audits)

        result = tool.parse_payload(payload, 'https://x.com')

        issues = [f.issue for f in result.fixes]
        assert issues[0] == 'LCP'
        assert issues[1] == 'Contrast'
        assert issues[2] == 'FCP'

    def test_perfect_score_no_fixes(self) -> None:
        """Given todos los audits con score=1.0, Then fixes vacios."""
        tool = LighthousePsi()
        audits = {
            'lcp': {'title': 'LCP', 'score': 1.0},
            'fcp': {'title': 'FCP', 'score': 1.0},
            'meta-description': {'title': 'Meta', 'score': 1.0},
            'color-contrast': {'title': 'Contrast', 'score': 1.0},
            'no-document-write': {'title': 'Doc write', 'score': 1.0},
            'inp': {'title': 'INP', 'score': 1.0},
        }
        payload = _payload(audits=audits)

        result = tool.parse_payload(payload, 'https://x.com')

        assert result.fixes == ()

    def test_severity_by_weight_thresholds(self) -> None:
        """
        Given audit con weight 10 (HIGH), weight 3 (MEDIUM), weight 1 (LOW),
        When parse_payload,
        Then los fixes tienen severity por weight (>=5 HIGH, >=2 MEDIUM,
            sino LOW).
        """
        tool = LighthousePsi()
        audits = {
            'lcp': {'title': 'LCP', 'score': 0.3},  # weight 10 -> HIGH
            'meta-description': {  # weight 3 -> MEDIUM
                'title': 'Meta',
                'score': 0,
            },
            'inp': {'title': 'INP', 'score': 0.4},  # weight 1 -> LOW
        }
        payload = _payload(audits=audits)

        result = tool.parse_payload(payload, 'https://x.com')

        by_issue = {f.issue: f.severity for f in result.fixes}
        assert by_issue['LCP'] == Severity.HIGH
        assert by_issue['Meta'] == Severity.MEDIUM
        assert by_issue['INP'] == Severity.LOW

    def test_missing_lighthouse_result_raises(self) -> None:
        """Given payload sin lighthouseResult, Then ParseError."""
        tool = LighthousePsi()

        with pytest.raises(ParseError, match='lighthouseResult'):
            tool.parse_payload({}, 'x')

    def test_api_error_field_raises(self) -> None:
        """Given payload con 'error', Then ParseError."""
        tool = LighthousePsi()

        with pytest.raises(ParseError, match='api error'):
            tool.parse_payload(
                {'error': {'message': 'Invalid url'}},
                'x',
            )

    def test_non_dict_payload_raises(self) -> None:
        """Given payload no-dict, Then ParseError."""
        tool = LighthousePsi()

        with pytest.raises(ParseError, match='not dict'):
            tool.parse_payload(['a', 'b'], 'x')  # type: ignore[arg-type]


class TestGetApiKey:
    """get_api_key: extraccion de PSI_API_KEY desde docker/env/dev-cli/.{env}.

    PSI_ENV controla cual archivo se lee. Sin .env existente -> None.
    """

    @pytest.fixture
    def fake_env_dir(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> Path:
        """Reemplaza PROJECT_ROOT/docker/env/dev-cli con un tmp_path."""
        env_dir = tmp_path / 'docker' / 'env' / 'dev-cli'
        env_dir.mkdir(parents=True)
        from ai_audit.tools import lighthouse_psi as mod

        monkeypatch.setattr(mod, 'PROJECT_ROOT', tmp_path)
        return env_dir

    def test_returns_key_when_set_in_local(
        self,
        fake_env_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given .local con PSI_API_KEY=abc, Then get_api_key=='abc'."""
        (fake_env_dir / '.local').write_text('PSI_API_KEY=abc123\n')
        monkeypatch.setenv('PSI_ENV', 'local')

        result = LighthousePsi().get_api_key()

        assert result == 'abc123'

    def test_returns_key_when_quoted(
        self,
        fake_env_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given valor entre comillas dobles, Then las strippea."""
        (fake_env_dir / '.prod').write_text('PSI_API_KEY="AIza-quoted"\n')
        monkeypatch.setenv('PSI_ENV', 'prod')

        result = LighthousePsi().get_api_key()

        assert result == 'AIza-quoted'

    def test_returns_none_when_env_file_missing(
        self,
        fake_env_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given .dev no existe, Then None."""
        monkeypatch.setenv('PSI_ENV', 'dev')

        result = LighthousePsi().get_api_key()

        assert result is None

    def test_returns_none_when_key_missing_from_file(
        self,
        fake_env_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given .local sin PSI_API_KEY, Then None."""
        (fake_env_dir / '.local').write_text('OTHER_KEY=xxx\n')
        monkeypatch.setenv('PSI_ENV', 'local')

        result = LighthousePsi().get_api_key()

        assert result is None

    def test_psi_env_defaults_to_prod_when_unset(
        self,
        fake_env_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given PSI_ENV no seteado, Then lee .prod (default)."""
        (fake_env_dir / '.prod').write_text('PSI_API_KEY=defaultkey\n')
        monkeypatch.delenv('PSI_ENV', raising=False)

        result = LighthousePsi().get_api_key()

        assert result == 'defaultkey'

    def test_extracts_only_first_match_when_duplicated(
        self,
        fake_env_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given .local con PSI_API_KEY duplicada, Then grep -m1 -> primera."""
        (fake_env_dir / '.local').write_text(
            'PSI_API_KEY=first\nPSI_API_KEY=second\n',
        )
        monkeypatch.setenv('PSI_ENV', 'local')

        result = LighthousePsi().get_api_key()

        assert result == 'first'

    def test_ignores_lines_that_contain_key_as_substring(
        self,
        fake_env_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given '#PSI_API_KEY' como comentario, Then NO matchea."""
        (fake_env_dir / '.local').write_text(
            '#PSI_API_KEY=comment\nPSI_API_KEY=real\n',
        )
        monkeypatch.setenv('PSI_ENV', 'local')

        result = LighthousePsi().get_api_key()

        assert result == 'real'


class TestMetadata:
    """Metadata estatica del tool."""

    def test_tool_name_and_no_storage_state_auth(self) -> None:
        """Given LighthousePsi(), Then TOOL_NAME esperado, NO requires_auth."""
        tool = LighthousePsi()

        assert tool.TOOL_NAME == 'lighthouse_psi'
        assert tool.REQUIRES_AUTH is False
