"""Scraper: Ahrefs AI Visibility Checker.

Mide brand mentions / citaciones del dominio en respuestas de las 5
plataformas IA: ChatGPT, Gemini, Perplexity, Copilot, Google AI
Overviews.

Requiere cuenta gratis (Ahrefs Webmaster Tools). El storageState se
guarda en docker/env/dev-cli/ai-audit/ahrefs.json (LOCAL-ONLY,
gitignored). El orquestador llama auth.check() ANTES de abrir el
browser context.
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


class Ahrefs:
    """Tool: scraper de Ahrefs AI Visibility Checker."""

    TOOL_NAME = 'ahrefs'
    REQUIRES_AUTH = True
    BASE_URL = 'https://ahrefs.com/ai-visibility-checker'

    async def scrape(self, page: Any, target: str) -> ToolResult:
        start = time.monotonic()
        await page.goto(self.BASE_URL, wait_until='domcontentloaded')
        await page.fill('input[name="domain"]', target)
        await page.click('button[type="submit"]')
        await page.wait_for_selector(
            '[data-test="platforms-count"], [data-test="login-required"]',
            timeout=90000,
        )
        html = await page.content()
        result = self.parse_dom(html, target)
        return _with_duration(result, start)

    def parse_dom(self, html: str, target: str) -> ToolResult:
        soup = BeautifulSoup(html, 'html.parser')

        if soup.find(attrs={'data-test': 'login-required'}):
            raise BlockedError('Ahrefs session expired (login required)')

        score_el = soup.find(attrs={'data-test': 'platforms-count'})
        if not score_el:
            raise ParseError('no platforms-count found')
        try:
            score = int(score_el.get_text(strip=True))
        except ValueError as exc:
            raise ParseError(f'score not int: {score_el.text!r}') from exc

        categories = _parse_platforms(soup)
        fixes = _parse_suggestions(soup)

        return ToolResult(
            tool=self.TOOL_NAME,
            target=target,
            status=Status.OK,
            score=score,
            categories=categories,
            fixes=fixes,
            raw_log_path=None,
        )


def _parse_platforms(soup: BeautifulSoup) -> dict[str, int | str]:
    """Por plataforma IA: nro de menciones (0+)."""
    out: dict[str, int | str] = {}
    for row in soup.find_all(attrs={'data-test': 'platform-row'}):
        name_el = row.find(attrs={'data-test': 'platform-name'})
        count_el = row.find(attrs={'data-test': 'mentions-count'})
        if not name_el or not count_el:
            continue
        name = name_el.get_text(strip=True)
        raw = count_el.get_text(strip=True)
        try:
            out[name] = int(raw)
        except ValueError:
            out[name] = raw
    return out


def _parse_suggestions(soup: BeautifulSoup) -> tuple[Fix, ...]:
    fixes: list[Fix] = []
    for item in soup.find_all(attrs={'data-test': 'suggestion-item'}):
        sev_el = item.find(attrs={'data-test': 'severity'})
        cat_el = item.find(attrs={'data-test': 'category'})
        issue_el = item.find(attrs={'data-test': 'issue'})
        fix_el = item.find(attrs={'data-test': 'fix'})
        if not (sev_el and cat_el and issue_el and fix_el):
            continue
        severity = _SEVERITY_MAP.get(
            sev_el.get_text(strip=True).lower(),
            Severity.LOW,
        )
        fixes.append(
            Fix(
                severity=severity,
                category=cat_el.get_text(strip=True),
                issue=issue_el.get_text(strip=True),
                fix=fix_el.get_text(strip=True),
                file=None,  # Ahrefs no propone archivos especificos
                reach=5,  # afecta visibility en las 5 plataformas
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
