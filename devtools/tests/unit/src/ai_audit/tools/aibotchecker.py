"""Unit tests for ai_audit.tools.aibotchecker.

Path mirroring: devtools/ai_audit/tools/aibotchecker.py -> este archivo.
"""

from pathlib import Path

import pytest

from ai_audit.tools.aibotchecker import AiBotChecker
from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status


pytestmark = pytest.mark.unit


_FIXTURES = Path(__file__).resolve().parent.parent / 'fixtures' / 'aibotchecker'


def _read_fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding='utf-8')


def test_parse_dom_when_sample_then_score_92() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.score == 92.
    """
    tool = AiBotChecker()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.score == 92


def test_parse_dom_when_sample_then_bots_per_status() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then categories tiene los 5 bots con su status exacto.
    """
    tool = AiBotChecker()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.categories == {
        'GPTBot': 'allow',
        'ClaudeBot': 'allow',
        'PerplexityBot': 'allow',
        'Google-Extended': 'allow',
        'CCBot': 'block',
    }


def test_parse_dom_when_sample_then_3_fixes_in_order() -> None:
    """
    Given fixture sample.html (3 issues),
    When parse_dom,
    Then result.fixes tiene 3 items: HIGH(CCBot), MEDIUM, LOW.
    """
    tool = AiBotChecker()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert len(result.fixes) == 3
    assert result.fixes[0].severity == Severity.HIGH
    assert result.fixes[0].category == 'CCBot'
    assert result.fixes[0].issue == 'blocked by robots.txt'
    assert result.fixes[0].file == 'apps/generic/public/robots.txt'
    assert result.fixes[1].severity == Severity.MEDIUM
    assert result.fixes[2].severity == Severity.LOW


def test_parse_dom_when_sample_then_status_ok() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.status == Status.OK.
    """
    tool = AiBotChecker()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.status == Status.OK
    assert result.tool == 'aibotchecker'


def test_parse_dom_when_challenge_then_raises_blocked() -> None:
    """
    Given fixture challenge.html,
    When parse_dom,
    Then raises BlockedError.
    """
    tool = AiBotChecker()
    html = _read_fixture('challenge.html')

    with pytest.raises(BlockedError, match='Cloudflare challenge'):
        tool.parse_dom(html, 'x')


def test_parse_dom_when_no_score_element_then_raises_parse_error() -> None:
    """
    Given HTML sin data-test=overall-score,
    When parse_dom,
    Then raises ParseError.
    """
    tool = AiBotChecker()

    with pytest.raises(ParseError, match='no overall-score found'):
        tool.parse_dom('<html><body>nothing</body></html>', 'x')


def test_metadata_when_inspected_then_anonimo_y_url_oficial() -> None:
    """
    Given la instancia AiBotChecker,
    When se inspecciona,
    Then TOOL_NAME, REQUIRES_AUTH y BASE_URL son los esperados.
    """
    tool = AiBotChecker()

    assert tool.TOOL_NAME == 'aibotchecker'
    assert tool.REQUIRES_AUTH is False
    assert tool.BASE_URL == 'https://aibotchecker.online'
