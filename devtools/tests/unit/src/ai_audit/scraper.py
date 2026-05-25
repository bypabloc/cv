"""Unit tests for ai_audit.scraper.

Path mirroring: devtools/ai_audit/scraper.py -> este archivo.
Mockea Playwright; NUNCA hace red.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ai_audit import auth
from ai_audit import scraper
from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import Status
from ai_audit.tools.base import ToolResult


pytestmark = pytest.mark.unit


def _ok_result(tool: str = 'isitagentready') -> ToolResult:
    return ToolResult(
        tool=tool,
        target='https://x/',
        status=Status.OK,
        score=78,
    )


async def test_scrape_with_retry_when_first_success_then_no_sleep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given un tool cuyo scrape retorna OK en el primer intento,
    When _scrape_with_retry,
    Then NO se invoca asyncio.sleep ni se reintenta.
    """
    tool = MagicMock()
    tool.TOOL_NAME = 'isitagentready'
    tool.REQUIRES_AUTH = False
    tool.scrape = AsyncMock(return_value=_ok_result())

    monkeypatch.setitem(scraper.REGISTRY, 'isitagentready', tool)

    sleep_mock = AsyncMock()
    monkeypatch.setattr('asyncio.sleep', sleep_mock)

    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    context.new_page = AsyncMock(return_value=page)
    context.close = AsyncMock()

    result = await scraper._scrape_with_retry(
        browser=browser,
        tool_name='isitagentready',
        target='https://x/',
    )

    assert result.status == Status.OK
    assert tool.scrape.await_count == 1
    sleep_mock.assert_not_awaited()


async def test_scrape_with_retry_when_3_blocked_then_blocked_and_waits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given un tool que lanza BlockedError 4 veces,
    When _scrape_with_retry,
    Then retorna status=BLOCKED y dispara waits [5, 15, 45]s en orden.
    """
    tool = MagicMock()
    tool.TOOL_NAME = 'isitagentready'
    tool.REQUIRES_AUTH = False
    tool.scrape = AsyncMock(side_effect=BlockedError('cf'))

    monkeypatch.setitem(scraper.REGISTRY, 'isitagentready', tool)

    sleep_calls: list[float] = []

    async def _capture_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr('asyncio.sleep', _capture_sleep)

    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    context.new_page = AsyncMock(return_value=page)
    context.close = AsyncMock()

    result = await scraper._scrape_with_retry(
        browser=browser,
        tool_name='isitagentready',
        target='https://x/',
    )

    assert result.status == Status.BLOCKED
    assert sleep_calls == [5.0, 15.0, 45.0]
    assert tool.scrape.await_count == 4


async def test_scrape_with_retry_when_auth_missing_then_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given un tool con REQUIRES_AUTH=True y auth.check -> MISSING,
    When _scrape_with_retry,
    Then retorna SKIPPED SIN abrir browser context (AC-6).
    """
    tool = MagicMock()
    tool.TOOL_NAME = 'ahrefs'
    tool.REQUIRES_AUTH = True

    monkeypatch.setitem(scraper.REGISTRY, 'ahrefs', tool)
    monkeypatch.setattr(
        auth,
        'check',
        lambda _name: auth.AuthState.MISSING,
    )

    browser = MagicMock()
    browser.new_context = AsyncMock()

    result = await scraper._scrape_with_retry(
        browser=browser,
        tool_name='ahrefs',
        target='https://x/',
    )

    assert result.status == Status.SKIPPED
    assert result.skipped_reason == 'storageState MISSING'
    browser.new_context.assert_not_awaited()


async def test_run_audit_when_2_targets_1_tool_then_sleeps_between(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given 2 targets x 1 tool,
    When run_audit,
    Then asyncio.sleep se invoca con TARGET_SLEEP entre targets
    (TOOL_SLEEP no aparece porque solo hay 1 tool).
    """
    tool = MagicMock()
    tool.TOOL_NAME = 'isitagentready'
    tool.REQUIRES_AUTH = False
    tool.scrape = AsyncMock(return_value=_ok_result())

    monkeypatch.setitem(scraper.REGISTRY, 'isitagentready', tool)

    sleep_calls: list[float] = []

    async def _capture_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr('asyncio.sleep', _capture_sleep)

    pw_manager = MagicMock()
    pw_manager.__aenter__ = AsyncMock(return_value=pw_manager)
    pw_manager.__aexit__ = AsyncMock(return_value=None)

    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()
    context.new_page = AsyncMock(return_value=page)
    context.close = AsyncMock()

    pw_manager.chromium = MagicMock()
    pw_manager.chromium.launch = AsyncMock(return_value=browser)

    with patch(
        'playwright.async_api.async_playwright', return_value=pw_manager
    ):
        results = await scraper.run_audit(
            targets=['https://a/', 'https://b/'],
            tool_names=['isitagentready'],
        )

    assert len(results) == 2
    assert all(r.status == Status.OK for r in results)
    assert scraper.TARGET_SLEEP_SECONDS in sleep_calls


def test_resolve_exit_code_when_all_ok_then_0() -> None:
    """
    Given todos OK,
    When resolve_exit_code,
    Then 0.
    """
    results = [_ok_result(), _ok_result()]

    assert scraper.resolve_exit_code(results) == 0


def test_resolve_exit_code_when_50pct_blocked_then_1() -> None:
    """
    Given 2 results: 1 OK, 1 BLOCKED,
    When resolve_exit_code,
    Then 1 (>= 50% BLOCKED dispara exit 1).
    """
    results = [
        _ok_result(),
        ToolResult(
            tool='ahrefs',
            target='x',
            status=Status.BLOCKED,
            score=None,
        ),
    ]

    assert scraper.resolve_exit_code(results) == 1


def test_resolve_exit_code_when_no_results_then_2() -> None:
    """
    Given lista vacia,
    When resolve_exit_code,
    Then 2 (error interno).
    """
    assert scraper.resolve_exit_code([]) == 2


def test_resolve_exit_code_when_skipped_then_0() -> None:
    """
    Given 2 results: 1 OK y 1 SKIPPED,
    When resolve_exit_code,
    Then 0 (SKIPPED no cuenta como BLOCKED/ERROR).
    """
    results = [
        _ok_result(),
        ToolResult(
            tool='ahrefs',
            target='x',
            status=Status.SKIPPED,
            score=None,
            skipped_reason='storageState MISSING',
        ),
    ]

    assert scraper.resolve_exit_code(results) == 0
