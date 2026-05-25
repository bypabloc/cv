"""Unit tests for ai_audit.tools.ahrefs.

Path mirroring: devtools/ai_audit/tools/ahrefs.py -> este archivo.
"""

from pathlib import Path

import pytest

from ai_audit.tools.ahrefs import Ahrefs
from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status


pytestmark = pytest.mark.unit


_FIXTURES = Path(__file__).resolve().parent.parent / 'fixtures' / 'ahrefs'


def _read_fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding='utf-8')


def test_parse_dom_when_sample_then_score_3() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.score == 3 (3 plataformas con menciones).
    """
    tool = Ahrefs()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.score == 3


def test_parse_dom_when_sample_then_5_platforms_with_counts() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then categories tiene las 5 plataformas con counts exactos.
    """
    tool = Ahrefs()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.categories == {
        'ChatGPT': 12,
        'Gemini': 0,
        'Perplexity': 8,
        'Copilot': 2,
        'Google AI Overviews': 0,
    }


def test_parse_dom_when_sample_then_2_fixes_ordered() -> None:
    """
    Given fixture sample.html (2 sugerencias),
    When parse_dom,
    Then result.fixes tiene 2 items HIGH y MEDIUM con reach=5.
    """
    tool = Ahrefs()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert len(result.fixes) == 2
    assert result.fixes[0].severity == Severity.HIGH
    assert result.fixes[0].category == 'Brand presence'
    assert result.fixes[0].issue == 'No mentions in Gemini'
    assert result.fixes[0].reach == 5
    assert result.fixes[0].file is None
    assert result.fixes[1].severity == Severity.MEDIUM


def test_parse_dom_when_sample_then_status_ok() -> None:
    """
    Given fixture sample.html,
    When parse_dom,
    Then result.status == Status.OK.
    """
    tool = Ahrefs()
    html = _read_fixture('sample.html')

    result = tool.parse_dom(html, 'https://the-full-stack.com/')

    assert result.status == Status.OK
    assert result.tool == 'ahrefs'


def test_parse_dom_when_login_required_then_raises_blocked() -> None:
    """
    Given fixture login_required.html,
    When parse_dom,
    Then raises BlockedError (orquestador puede marcar SKIPPED).
    """
    tool = Ahrefs()
    html = _read_fixture('login_required.html')

    with pytest.raises(BlockedError, match='Ahrefs session expired'):
        tool.parse_dom(html, 'x')


def test_parse_dom_when_no_score_then_raises_parse_error() -> None:
    """
    Given HTML sin data-test=platforms-count,
    When parse_dom,
    Then raises ParseError.
    """
    tool = Ahrefs()

    with pytest.raises(ParseError, match='no platforms-count found'):
        tool.parse_dom('<html><body>x</body></html>', 'x')


def test_metadata_when_inspected_then_requires_auth() -> None:
    """
    Given la instancia Ahrefs,
    When se inspecciona,
    Then REQUIRES_AUTH es True y la URL es la oficial.
    """
    tool = Ahrefs()

    assert tool.TOOL_NAME == 'ahrefs'
    assert tool.REQUIRES_AUTH is True
    assert tool.BASE_URL == 'https://ahrefs.com/ai-visibility-checker'
