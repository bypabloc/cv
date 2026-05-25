"""Scraper: isitagentready.com (Cloudflare).

Audita preparacion para agentes IA (MCP, robots.txt Content Signals,
Markdown negotiation, etc.) en 5 categorias: Discoverability, Content
Accessibility, Bot Access Control, Protocol Discovery, Commerce
Standards.

Anonima (sin login). Selectores capturados via fixture HTML real (ver
tests/unit/src/ai_audit/fixtures/isitagentready/).
"""

from pathlib import Path
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


class IsItAgentReady:
    """Tool: scraper de isitagentready.com."""

    TOOL_NAME = 'isitagentready'
    REQUIRES_AUTH = False
    BASE_URL = 'https://isitagentready.com'

    async def scrape(self, page: Any, target: str) -> ToolResult:
        """Navega, audita y parsea. Lanza BlockedError ante challenge."""
        start = time.monotonic()
        await page.goto(self.BASE_URL, wait_until='domcontentloaded')
        await page.fill('input[name="url"]', target)
        await page.click('button[type="submit"]')
        await page.wait_for_selector(
            '[data-test="score-value"], #cf-challenge-form',
            timeout=60000,
        )
        html = await page.content()
        result = self.parse_dom(html, target)
        return _with_duration(result, start)

    def parse_dom(self, html: str, target: str) -> ToolResult:
        """Extrae score + categorias + top fixes del HTML capturado."""
        soup = BeautifulSoup(html, 'html.parser')

        if soup.find(id='cf-challenge-form'):
            raise BlockedError('Cloudflare challenge')

        score_el = soup.find(attrs={'data-test': 'score-value'})
        if not score_el:
            raise ParseError('no score-value found')
        try:
            score = int(score_el.get_text(strip=True))
        except ValueError as exc:
            raise ParseError(f'score not int: {score_el.text!r}') from exc

        categories = _parse_categories(soup)
        fixes = _parse_fixes(soup)

        return ToolResult(
            tool=self.TOOL_NAME,
            target=target,
            status=Status.OK,
            score=score,
            categories=categories,
            fixes=fixes,
            raw_log_path=None,
        )


def _parse_categories(soup: BeautifulSoup) -> dict[str, int | str]:
    out: dict[str, int | str] = {}
    for row in soup.find_all(attrs={'data-test': 'category-row'}):
        name_el = row.find(attrs={'data-test': 'cat-name'})
        score_el = row.find(attrs={'data-test': 'cat-score'})
        if not name_el or not score_el:
            continue
        name = name_el.get_text(strip=True)
        raw = score_el.get_text(strip=True)
        try:
            out[name] = int(raw)
        except ValueError:
            out[name] = raw
    return out


def _parse_fixes(soup: BeautifulSoup) -> tuple[Fix, ...]:
    fixes: list[Fix] = []
    for item in soup.find_all(attrs={'data-test': 'fix-item'}):
        sev_el = item.find(attrs={'data-test': 'severity'})
        cat_el = item.find(attrs={'data-test': 'category'})
        issue_el = item.find(attrs={'data-test': 'issue'})
        fix_el = item.find(attrs={'data-test': 'fix'})
        if not (sev_el and cat_el and issue_el and fix_el):
            continue
        severity = _SEVERITY_MAP.get(
            sev_el.get_text(strip=True).lower(), Severity.LOW,
        )
        file_el = item.find(attrs={'data-test': 'file'})
        fixes.append(
            Fix(
                severity=severity,
                category=cat_el.get_text(strip=True),
                issue=issue_el.get_text(strip=True),
                fix=fix_el.get_text(strip=True),
                file=file_el.get_text(strip=True) if file_el else None,
                reach=_severity_reach(severity),
            )
        )
    return tuple(fixes[:5])


def _severity_reach(severity: Severity) -> int:
    """Heuristica simple: high=8, medium=4, low=1."""
    return {Severity.HIGH: 8, Severity.MEDIUM: 4, Severity.LOW: 1}[severity]


def _with_duration(result: ToolResult, start: float) -> ToolResult:
    """Devuelve un ToolResult con duration_ms calculado."""
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
