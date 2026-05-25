"""Scraper: aibotchecker.online.

Mide accesibilidad real per-agent (GPTBot, ClaudeBot, PerplexityBot,
OAI-SearchBot, ChatGPT-User, Anthropic-Claude-Web, Google-Extended,
CCBot, etc.). Score agregado = % de bots que tienen acceso correcto.

Anonima. Selectores capturados via fixture HTML real (ver
tests/unit/src/ai_audit/fixtures/aibotchecker/).
"""

import time
from typing import Any

from bs4 import BeautifulSoup

from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import Fix
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import ToolResult


_SEVERITY_MAP = {
    'high': Severity.HIGH,
    'medium': Severity.MEDIUM,
    'low': Severity.LOW,
}


class AiBotChecker:
    """Tool: scraper de aibotchecker.online."""

    TOOL_NAME = 'aibotchecker'
    REQUIRES_AUTH = False
    BASE_URL = 'https://aibotchecker.online'

    async def scrape(self, page: Any, target: str) -> ToolResult:
        start = time.monotonic()
        await page.goto(self.BASE_URL, wait_until='domcontentloaded')
        await page.fill('input[name="url"]', target)
        await page.click('button[type="submit"]')
        await page.wait_for_selector(
            '[data-test="overall-score"], #cf-challenge-form',
            timeout=60000,
        )
        html = await page.content()
        result = self.parse_dom(html, target)
        return _with_duration(result, start)

    def parse_dom(self, html: str, target: str) -> ToolResult:
        soup = BeautifulSoup(html, 'html.parser')

        if soup.find(id='cf-challenge-form'):
            raise BlockedError('Cloudflare challenge')

        score_el = soup.find(attrs={'data-test': 'overall-score'})
        if not score_el:
            raise ParseError('no overall-score found')
        try:
            score = int(score_el.get_text(strip=True))
        except ValueError as exc:
            raise ParseError(f'score not int: {score_el.text!r}') from exc

        bot_categories = _parse_bots(soup)
        fixes = _parse_issues(soup)

        return ToolResult(
            tool=self.TOOL_NAME,
            target=target,
            status=Status.OK,
            score=score,
            categories=bot_categories,
            fixes=fixes,
            raw_log_path=None,
        )


def _parse_bots(soup: BeautifulSoup) -> dict[str, int | str]:
    """Por bot: 'allow' / 'block'. Lo devuelve como dict[bot, str]."""
    out: dict[str, int | str] = {}
    for row in soup.find_all(attrs={'data-test': 'bot-row'}):
        name_el = row.find(attrs={'data-test': 'bot-name'})
        status_el = row.find(attrs={'data-test': 'bot-status'})
        if not name_el or not status_el:
            continue
        out[name_el.get_text(strip=True)] = status_el.get_text(strip=True)
    return out


def _parse_issues(soup: BeautifulSoup) -> tuple[Fix, ...]:
    fixes: list[Fix] = []
    for item in soup.find_all(attrs={'data-test': 'issue-item'}):
        sev_el = item.find(attrs={'data-test': 'severity'})
        bot_el = item.find(attrs={'data-test': 'bot'})
        issue_el = item.find(attrs={'data-test': 'issue'})
        fix_el = item.find(attrs={'data-test': 'fix'})
        if not (sev_el and bot_el and issue_el and fix_el):
            continue
        severity = _SEVERITY_MAP.get(
            sev_el.get_text(strip=True).lower(),
            Severity.LOW,
        )
        file_el = item.find(attrs={'data-test': 'file'})
        # En aibotchecker, "category" = el bot afectado (Bot Access scope)
        fixes.append(
            Fix(
                severity=severity,
                category=bot_el.get_text(strip=True),
                issue=issue_el.get_text(strip=True),
                fix=fix_el.get_text(strip=True),
                file=file_el.get_text(strip=True) if file_el else None,
                reach=1,  # afecta 1 bot por item; total reach via aggregation
            )
        )
    return tuple(fixes[:5])


def _with_duration(result: ToolResult, start: float) -> ToolResult:
    duration = int((time.monotonic() - start) * 1000)
    return ToolResult(
        tool=result.tool,
        target=result.target,
        status=result.status,
        score=result.score,
        categories=result.categories,
        fixes=result.fixes,
        raw_log_path=result.raw_log_path,
        duration_ms=duration,
        skipped_reason=result.skipped_reason,
        error_message=result.error_message,
    )
