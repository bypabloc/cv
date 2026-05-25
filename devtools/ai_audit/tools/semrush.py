"""Scraper: Semrush AI Visibility Audit.

Combina technical blocking + content audit + trafico real desde
plataformas IA en un score 0-100. Categorias: Technical, Content,
Visibility.

Requiere cuenta gratis Semrush. storageState en
docker/env/dev-cli/ai-audit/semrush.json (LOCAL-ONLY, gitignored).
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


class Semrush:
    """Tool: scraper de Semrush AI Visibility Audit."""

    TOOL_NAME = 'semrush'
    REQUIRES_AUTH = True
    BASE_URL = 'https://www.semrush.com/ai-visibility-audit'

    async def scrape(self, page: Any, target: str) -> ToolResult:
        start = time.monotonic()
        await page.goto(self.BASE_URL, wait_until='domcontentloaded')
        await page.fill('input[name="domain"]', target)
        await page.click('button[type="submit"]')
        await page.wait_for_selector(
            '[data-test="ai-score"], [data-test="login-required"]',
            timeout=90000,
        )
        html = await page.content()
        result = self.parse_dom(html, target)
        return _with_duration(result, start)

    def parse_dom(self, html: str, target: str) -> ToolResult:
        soup = BeautifulSoup(html, 'html.parser')

        if soup.find(attrs={'data-test': 'login-required'}):
            raise BlockedError('Semrush session expired (login required)')

        score_el = soup.find(attrs={'data-test': 'ai-score'})
        if not score_el:
            raise ParseError('no ai-score found')
        try:
            score = int(score_el.get_text(strip=True))
        except ValueError as exc:
            raise ParseError(f'score not int: {score_el.text!r}') from exc

        categories = _parse_categories(soup)
        fixes = _parse_issues(soup)

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
    """3 categorias: Technical, Content, Visibility (0-100)."""
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


def _parse_issues(soup: BeautifulSoup) -> tuple[Fix, ...]:
    fixes: list[Fix] = []
    for item in soup.find_all(attrs={'data-test': 'issue-item'}):
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
    """Heuristica: high=6, medium=3, low=1 (rango menor que isitagentready)."""
    return {Severity.HIGH: 6, Severity.MEDIUM: 3, Severity.LOW: 1}[severity]


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
