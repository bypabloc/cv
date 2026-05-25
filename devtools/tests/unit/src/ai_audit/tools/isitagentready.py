"""Unit tests for ai_audit.tools.isitagentready.

Path mirroring: devtools/ai_audit/tools/isitagentready.py -> este archivo.
"""

from pathlib import Path

import pytest

from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.isitagentready import IsItAgentReady


pytestmark = pytest.mark.unit


_FIXTURES = (
    Path(__file__).resolve().parent.parent / 'fixtures' / 'isitagentready'
)


def _read_fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding='utf-8')


def test_parse_dom_when_sample_then_score_78() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.score == 78.
    """
    tool = IsItAgentReady()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.score == 78


def test_parse_dom_when_sample_then_categories_complete() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.categories tiene las 5 categorias con sus scores exactos.
    """
    tool = IsItAgentReady()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.categories == {
        'Discoverability': 90,
        'Content Accessibility': 85,
        'Bot Access Control': 60,
        'Protocol Discovery': 70,
        'Commerce Standards': 80,
    }


def test_parse_dom_when_sample_then_5_fixes_ordered_by_dom_order() -> None:
    """
    Given fixture sample.html (5 fix-items),
    When parse_dom,
    Then result.fixes tiene 5 items con severity correcta.
    """
    tool = IsItAgentReady()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert len(result.fixes) == 5
    assert result.fixes[0].severity == Severity.HIGH
    assert result.fixes[0].category == 'Bot Access Control'
    assert result.fixes[0].issue == 'robots.txt missing GPTBot allow rule'
    assert result.fixes[0].file == 'apps/generic/public/robots.txt'
    assert result.fixes[0].reach == 8
    assert result.fixes[4].severity == Severity.LOW


def test_parse_dom_when_sample_then_status_ok() -> None:
    """
    Given fixture sample.html (sin challenge),
    When parse_dom,
    Then result.status == Status.OK.
    """
    tool = IsItAgentReady()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.status == Status.OK
    assert result.tool == 'isitagentready'


def test_parse_dom_when_challenge_then_raises_blocked() -> None:
    """
    Given fixture challenge.html (cf-challenge-form presente),
    When parse_dom,
    Then raises BlockedError.
    """
    tool = IsItAgentReady()
    html = _read_fixture('challenge.html')

    with pytest.raises(BlockedError, match='Cloudflare challenge'):
        tool.parse_dom(html, 'https://the-full-stack.com/')


def test_parse_dom_when_no_score_element_then_raises_parse_error() -> None:
    """
    Given HTML sin data-test=score-value,
    When parse_dom,
    Then raises ParseError.
    """
    tool = IsItAgentReady()

    with pytest.raises(ParseError, match='no score-value found'):
        tool.parse_dom('<html><body><p>nothing</p></body></html>', 'x')


def test_metadata_when_inspected_then_anonimo_y_url_oficial() -> None:
    """
    Given la instancia IsItAgentReady,
    When se inspecciona,
    Then TOOL_NAME, REQUIRES_AUTH y BASE_URL son los esperados.
    """
    tool = IsItAgentReady()

    assert tool.TOOL_NAME == 'isitagentready'
    assert tool.REQUIRES_AUTH is False
    assert tool.BASE_URL == 'https://isitagentready.com'
