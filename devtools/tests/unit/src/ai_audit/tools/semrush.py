"""Unit tests for ai_audit.tools.semrush.

Path mirroring: devtools/ai_audit/tools/semrush.py -> este archivo.
"""

from pathlib import Path

import pytest

from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.semrush import Semrush


pytestmark = pytest.mark.unit


_FIXTURES = Path(__file__).resolve().parent.parent / 'fixtures' / 'semrush'


def _read_fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding='utf-8')


def test_parse_dom_when_sample_then_score_65() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.score == 65.
    """
    tool = Semrush()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.score == 65


def test_parse_dom_when_sample_then_3_categories_with_scores() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then categories tiene Technical, Content, Visibility con scores
    exactos.
    """
    tool = Semrush()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.categories == {
        'Technical': 80,
        'Content': 55,
        'Visibility': 60,
    }


def test_parse_dom_when_sample_then_3_fixes_in_severity_order() -> None:
    """
    Given fixture sample.html (3 issues),
    When parse_dom,
    Then result.fixes tiene 3 items con severidad HIGH/MEDIUM/LOW.
    """
    tool = Semrush()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert len(result.fixes) == 3
    assert result.fixes[0].severity == Severity.HIGH
    assert result.fixes[0].category == 'Content'
    assert result.fixes[0].issue == 'Missing structured data (JSON-LD Article)'
    assert result.fixes[0].reach == 6
    assert result.fixes[1].severity == Severity.MEDIUM
    assert result.fixes[1].reach == 3
    assert result.fixes[2].severity == Severity.LOW
    assert result.fixes[2].reach == 1


def test_parse_dom_when_sample_then_status_ok() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.status == Status.OK.
    """
    tool = Semrush()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.status == Status.OK
    assert result.tool == 'semrush'


def test_parse_dom_when_login_required_then_raises_blocked() -> None:
    """
    Given fixture login_required.html,
    When parse_dom,
    Then raises BlockedError.
    """
    tool = Semrush()
    html = _read_fixture('login_required.html')

    with pytest.raises(BlockedError, match='Semrush session expired'):
        tool.parse_dom(html, 'x')


def test_parse_dom_when_no_score_then_raises_parse_error() -> None:
    """
    Given HTML sin data-test=ai-score,
    When parse_dom,
    Then raises ParseError.
    """
    tool = Semrush()

    with pytest.raises(ParseError, match='no ai-score found'):
        tool.parse_dom('<html><body>x</body></html>', 'x')


def test_metadata_when_inspected_then_requires_auth() -> None:
    """
    Given la instancia Semrush,
    When se inspecciona,
    Then REQUIRES_AUTH es True y la URL es la oficial.
    """
    tool = Semrush()

    assert tool.TOOL_NAME == 'semrush'
    assert tool.REQUIRES_AUTH is True
    assert tool.BASE_URL == 'https://www.semrush.com/ai-visibility-audit'
