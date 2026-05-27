"""Scraper: isitagentready.com (Cloudflare AI readiness audit).

Consume el endpoint JSON `POST /api/scan` directo en vez de scrapear
DOM dinamico: la pagina renderiza client-side haciendo fetch a esa
misma API, asi que es la fuente de verdad estable.

Anonima (sin login). El endpoint acepta cualquier User-Agent. Devuelve
JSON con: level (0-5), levelName, checks por categoria con status
pass/fail/neutral, nextLevel.requirements (lo que bloquea el upgrade).
"""

import time
from typing import Any

import httpx

from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import Fix
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import ToolResult


_API_URL = 'https://isitagentready.com/api/scan'
# El scan demora 10-30s en promedio; margen amplio para sitios lentos.
_TIMEOUT_SECONDS = 90.0

# Reach por severity (sincronizado con report.SEVERITY_WEIGHT).
_REACH_HIGH = 8
_REACH_MEDIUM = 4
_REACH_LOW = 1

_TOP_FIXES = 5


class IsItAgentReady:
    """Tool: cliente del endpoint JSON oficial de isitagentready.com."""

    TOOL_NAME = 'isitagentready'
    REQUIRES_AUTH = False
    BASE_URL = 'https://isitagentready.com'

    async def scrape(self, page: Any, target: str) -> ToolResult:
        """POST a /api/scan y parsea JSON. Lanza BlockedError si Cloudflare bloquea."""
        del page  # No usamos browser: el endpoint es JSON publico.
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    _API_URL,
                    json={'url': target},
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': (
                            'Mozilla/5.0 (compatible; portfolio-ai-audit/1.0)'
                        ),
                    },
                )
        except httpx.TimeoutException as exc:
            raise BlockedError(f'timeout: {exc}') from exc
        except httpx.HTTPError as exc:
            raise ParseError(f'http error: {exc}') from exc

        if response.status_code in (403, 429):
            raise BlockedError(f'http {response.status_code}')
        if response.status_code >= 500:
            raise BlockedError(f'http {response.status_code}')
        if response.status_code != 200:
            raise ParseError(
                f'http {response.status_code}: {response.text[:200]}'
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ParseError(f'invalid json: {exc}') from exc

        result = self.parse_payload(payload, target)
        return _with_duration(result, start)

    def parse_payload(
        self,
        payload: dict[str, Any],
        target: str,
    ) -> ToolResult:
        """Pure parser del JSON de /api/scan. Testeable sin red."""
        if not isinstance(payload, dict):
            raise ParseError(f'payload not dict: {type(payload).__name__}')

        if 'error' in payload:
            raise ParseError(f'api error: {payload["error"]}')

        level = payload.get('level')
        if not isinstance(level, int):
            raise ParseError(f'missing/invalid level: {level!r}')

        checks = payload.get('checks')
        if not isinstance(checks, dict):
            raise ParseError(f'missing/invalid checks: {type(checks).__name__}')

        categories = _build_categories(checks)
        fixes = _build_fixes(payload)

        return ToolResult(
            tool=self.TOOL_NAME,
            target=target,
            status=Status.OK,
            score=level,
            categories=categories,
            fixes=fixes,
        )


def _build_categories(
    checks: dict[str, Any],
) -> dict[str, int | str]:
    """Por categoria: % de checks `pass` (excluye neutral del divisor)."""
    out: dict[str, int | str] = {}
    for cat_name, cat_checks in checks.items():
        if not isinstance(cat_checks, dict) or not cat_checks:
            continue
        counted = [
            c
            for c in cat_checks.values()
            if isinstance(c, dict) and c.get('status') in ('pass', 'fail')
        ]
        if not counted:
            out[cat_name] = 'n/a'
            continue
        passed = sum(1 for c in counted if c.get('status') == 'pass')
        out[cat_name] = round(passed / len(counted) * 100)
    return out


def _build_fixes(payload: dict[str, Any]) -> tuple[Fix, ...]:
    """Top fixes: nextLevel.requirements (HIGH) + otros checks fail (MEDIUM)."""
    fixes: list[Fix] = []
    seen: set[str] = set()
    checks = payload.get('checks') or {}

    next_level = payload.get('nextLevel') or {}
    for req in next_level.get('requirements') or []:
        if not isinstance(req, dict):
            continue
        check_name = req.get('check')
        if not isinstance(check_name, str) or check_name in seen:
            continue
        seen.add(check_name)
        fixes.append(
            Fix(
                severity=Severity.HIGH,
                category=_category_for_check(check_name, checks),
                issue=(
                    req.get('description')
                    or f'{check_name} requerido para subir de nivel'
                ),
                fix=req.get('shortPrompt') or req.get('prompt') or '',
                file=None,
                reach=_REACH_HIGH,
            )
        )

    for cat_name, cat_checks in checks.items():
        if not isinstance(cat_checks, dict):
            continue
        for check_name, check in cat_checks.items():
            if check_name in seen:
                continue
            if not isinstance(check, dict):
                continue
            if check.get('status') != 'fail':
                continue
            seen.add(check_name)
            fixes.append(
                Fix(
                    severity=Severity.MEDIUM,
                    category=cat_name,
                    issue=check.get('message') or check_name,
                    fix='',
                    file=None,
                    reach=_REACH_MEDIUM,
                )
            )

    return tuple(fixes[:_TOP_FIXES])


def _category_for_check(
    check_name: str,
    checks: dict[str, Any],
) -> str:
    for cat_name, cat_checks in checks.items():
        if isinstance(cat_checks, dict) and check_name in cat_checks:
            return cat_name
    return 'unknown'


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
