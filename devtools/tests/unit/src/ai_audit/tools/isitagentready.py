"""Unit tests for ai_audit.tools.isitagentready.

Path mirroring: devtools/ai_audit/tools/isitagentready.py -> este archivo.

El tool consume el endpoint JSON POST /api/scan directo (no scrapea
DOM). Los tests usan un fixture real capturado del API contra
the-full-stack.com (level=2 Bot-Aware, con `pass`/`fail`/`neutral`
mezclados y `nextLevel.requirements` poblado).
"""

import json
from pathlib import Path

from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.isitagentready import IsItAgentReady
import pytest


pytestmark = pytest.mark.unit


_FIXTURES = (
    Path(__file__).resolve().parent.parent / 'fixtures' / 'isitagentready'
)
_REAL_PAYLOAD = _FIXTURES / 'api-real-level2.json'


def _load_payload(name: str = 'api-real-level2.json') -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding='utf-8'))


class TestParsePayloadReal:
    """Parsea un fixture real del API (the-full-stack.com, level=2)."""

    def test_score_equals_level_value(self) -> None:
        """
        Given el fixture real (level=2),
        When parse_payload,
        Then result.score == 2 (escala 0-5 del API).
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        assert result.score == 2

    def test_status_is_ok(self) -> None:
        """
        Given el fixture real,
        When parse_payload,
        Then result.status == OK y tool == 'isitagentready'.
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        assert result.status == Status.OK
        assert result.tool == 'isitagentready'
        assert result.target == 'https://the-full-stack.com'

    def test_categories_match_api_taxonomy(self) -> None:
        """
        Given el fixture real,
        When parse_payload,
        Then categories incluye las 5 keys del API (discoverability,
            contentAccessibility, botAccessControl, discovery, commerce).
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        expected_keys = {
            'discoverability',
            'contentAccessibility',
            'botAccessControl',
            'discovery',
            'commerce',
        }
        assert set(result.categories) == expected_keys

    def test_category_percent_computation_excludes_neutral(self) -> None:
        """
        Given el fixture real:
          - discoverability: 2 pass + 1 fail (3 contables) -> 67%
          - contentAccessibility: 0 pass + 1 fail (1 contable) -> 0%
          - botAccessControl: 2 pass + 1 neutral (2 contables, 1 excl) -> 100%
          - discovery: 0 pass + 7 fail (7 contables) -> 0%
          - commerce: 5 neutral (0 contables) -> 'n/a'
        When parse_payload,
        Then los porcentajes son exactos y commerce es 'n/a'.
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        assert result.categories['discoverability'] == 67
        assert result.categories['contentAccessibility'] == 0
        assert result.categories['botAccessControl'] == 100
        assert result.categories['discovery'] == 0
        assert result.categories['commerce'] == 'n/a'

    def test_top_fixes_capped_at_5(self) -> None:
        """
        Given el fixture real (>5 checks fail + requirements de nextLevel),
        When parse_payload,
        Then result.fixes contiene exactamente 5 items (TOP_FIXES cap).
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        assert len(result.fixes) == 5

    def test_first_fix_comes_from_next_level_requirement(self) -> None:
        """
        Given el fixture real (nextLevel.requirements no vacio),
        When parse_payload,
        Then el primer Fix tiene severity=HIGH y reach=8 (next-level priority).
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        assert result.fixes[0].severity == Severity.HIGH
        assert result.fixes[0].reach == 8

    def test_first_fix_category_resolved_from_checks(self) -> None:
        """
        Given el fixture real (markdownNegotiation -> contentAccessibility),
        When parse_payload,
        Then el primer Fix (markdownNegotiation) tiene category contentAccessibility.
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        assert result.fixes[0].category == 'contentAccessibility'

    def test_first_fix_uses_short_prompt_as_fix_text(self) -> None:
        """
        Given el fixture real (req con shortPrompt presente),
        When parse_payload,
        Then result.fixes[0].fix == el shortPrompt del API.
        """
        tool = IsItAgentReady()
        payload = _load_payload()
        expected = payload['nextLevel']['requirements'][0]['shortPrompt']

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        assert result.fixes[0].fix == expected


class TestParsePayloadEdgeCases:
    """Manejo de payloads invalidos / parciales."""

    def test_missing_level_raises_parse_error(self) -> None:
        """
        Given un payload sin 'level',
        When parse_payload,
        Then ParseError.
        """
        tool = IsItAgentReady()

        with pytest.raises(ParseError, match='level'):
            tool.parse_payload({'checks': {}}, 'x')

    def test_level_not_int_raises_parse_error(self) -> None:
        """
        Given un payload con level no-int (ej. string),
        When parse_payload,
        Then ParseError.
        """
        tool = IsItAgentReady()

        with pytest.raises(ParseError, match='level'):
            tool.parse_payload({'level': 'high', 'checks': {}}, 'x')

    def test_missing_checks_raises_parse_error(self) -> None:
        """
        Given un payload con level pero sin 'checks',
        When parse_payload,
        Then ParseError.
        """
        tool = IsItAgentReady()

        with pytest.raises(ParseError, match='checks'):
            tool.parse_payload({'level': 3}, 'x')

    def test_api_error_field_raises_parse_error(self) -> None:
        """
        Given un payload con campo 'error' (la API reporta fallo),
        When parse_payload,
        Then ParseError con el mensaje del API.
        """
        tool = IsItAgentReady()

        with pytest.raises(ParseError, match='invalid url'):
            tool.parse_payload({'error': 'invalid url'}, 'x')

    def test_non_dict_payload_raises_parse_error(self) -> None:
        """
        Given un payload no-dict (ej. lista),
        When parse_payload,
        Then ParseError.
        """
        tool = IsItAgentReady()

        with pytest.raises(ParseError, match='not dict'):
            tool.parse_payload(['no', 'es', 'dict'], 'x')  # type: ignore[arg-type]

    def test_empty_checks_returns_zero_categories(self) -> None:
        """
        Given un payload con checks={} (sin categorias),
        When parse_payload,
        Then categories vacio, fixes vacios, status OK, score == level.
        """
        tool = IsItAgentReady()

        result = tool.parse_payload({'level': 0, 'checks': {}}, 'x')

        assert result.score == 0
        assert result.categories == {}
        assert result.fixes == ()
        assert result.status == Status.OK


class TestParsePayloadFixesPriority:
    """Verifica que los fixes se ordenan: nextLevel primero, luego fails."""

    def test_fix_after_requirements_has_medium_severity(self) -> None:
        """
        Given el fixture real (nextLevel solo cubre markdownNegotiation; el
            resto de fails entran como MEDIUM),
        When parse_payload,
        Then los Fix despues del primero tienen severity=MEDIUM y reach=4.
        """
        tool = IsItAgentReady()
        payload = _load_payload()

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        for fix in result.fixes[1:]:
            assert fix.severity == Severity.MEDIUM
            assert fix.reach == 4

    def test_neutral_checks_never_become_fixes(self) -> None:
        """
        Given el fixture real (checks con status='neutral' como webBotAuth),
        When parse_payload,
        Then ningun Fix.issue/category corresponde a un check neutral.
        """
        tool = IsItAgentReady()
        payload = _load_payload()
        neutral_issues = {
            c['message']
            for cat_checks in payload['checks'].values()
            for c in cat_checks.values()
            if c.get('status') == 'neutral'
        }

        result = tool.parse_payload(payload, 'https://the-full-stack.com')

        fix_issues = {fix.issue for fix in result.fixes}
        assert fix_issues.isdisjoint(neutral_issues)


class TestMetadata:
    """Metadata estatica del tool."""

    def test_tool_name_and_no_auth_and_base_url(self) -> None:
        """
        Given la instancia IsItAgentReady,
        When se inspecciona,
        Then TOOL_NAME='isitagentready', REQUIRES_AUTH=False,
            BASE_URL='https://isitagentready.com'.
        """
        tool = IsItAgentReady()

        assert tool.TOOL_NAME == 'isitagentready'
        assert tool.REQUIRES_AUTH is False
        assert tool.BASE_URL == 'https://isitagentready.com'
