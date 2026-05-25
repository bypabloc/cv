"""Tool `lighthouse_psi`: Google PageSpeed Insights API.

API: `https://www.googleapis.com/pagespeedonline/v5/runPagespeed`
Auth: API key gratis (sin tarjeta) desde Google Cloud Console.
Free tier: 25 000 requests/dia, 100 req/100s (mas que suficiente).

Lee la API key de `docker/env/dev-cli/.{env}` con la key `PSI_API_KEY`
extraida via shell (NUNCA cargamos el archivo completo —
ver `.claude/rules/env-files.md`). Si la key no esta, devuelve SKIPPED.

Devuelve el score normalizado 0-100 de las 2 categorias relevantes:
performance y seo.
"""

import os
import subprocess
import time
from typing import Any

import httpx
from shared.paths import PROJECT_ROOT

from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import Fix
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import ToolResult


_PSI_URL = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
_TIMEOUT_SECONDS = 90.0
_CATEGORIES = ('performance', 'seo', 'accessibility', 'best-practices')

# Top audits con weight > 0 a reportar como fix accionable
_TOP_FIXES = 5


class LighthousePsi:
    """Tool: cliente del PageSpeed Insights API (Google)."""

    TOOL_NAME = 'lighthouse_psi'
    REQUIRES_AUTH = False  # auth via API key env, no via storageState
    BASE_URL = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'

    def get_api_key(self) -> str | None:
        """Resuelve PSI_API_KEY desde docker/env/dev-cli/.{env}.

        El env se lee de PSI_ENV (seteado por main.py) con fallback
        'prod'. Extraccion via `grep -m1 '^PSI_API_KEY='` para nunca
        volcar el archivo completo al contexto (cumple env-files.md).
        Devuelve None si no esta seteada o el archivo no existe.
        """
        env = os.environ.get('PSI_ENV', 'prod')
        env_file = PROJECT_ROOT / 'docker' / 'env' / 'dev-cli' / f'.{env}'
        if not env_file.exists():
            return None
        try:
            result = subprocess.run(  # noqa: S603
                ['grep', '-m1', '^PSI_API_KEY=', str(env_file)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return None
        line = result.stdout.strip()
        _, _, value = line.partition('=')
        value = value.strip().strip('"').strip("'")
        return value or None

    async def scrape(self, page: Any, target: str) -> ToolResult:
        """GET al PSI API. SKIPPED si no hay API key."""
        del page
        start = time.monotonic()

        api_key = self.get_api_key()
        if not api_key:
            env = os.environ.get('PSI_ENV', 'prod')
            return ToolResult(
                tool=self.TOOL_NAME,
                target=target,
                status=Status.SKIPPED,
                score=None,
                skipped_reason=(
                    f'PSI_API_KEY missing en docker/env/dev-cli/.{env} '
                    '(obtener en https://console.cloud.google.com/apis/credentials)'
                ),
            )

        params: list[tuple[str, str]] = [('url', target), ('key', api_key)]
        params.extend(
            ('category', cat.upper().replace('-', '_')) for cat in _CATEGORIES
        )

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.get(_PSI_URL, params=params)
        except httpx.TimeoutException as exc:
            raise BlockedError(f'timeout: {exc}') from exc
        except httpx.HTTPError as exc:
            raise ParseError(f'http error: {exc}') from exc

        if response.status_code == 403:
            raise BlockedError('http 403: PSI_API_KEY invalido o sin quota')
        if response.status_code == 429:
            raise BlockedError('http 429: rate-limited por PSI')
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
        """Pure parser del JSON de PSI v5."""
        if not isinstance(payload, dict):
            raise ParseError(f'payload not dict: {type(payload).__name__}')

        if 'error' in payload:
            err = payload['error']
            msg = err.get('message') if isinstance(err, dict) else str(err)
            raise ParseError(f'api error: {msg}')

        result_block = payload.get('lighthouseResult')
        if not isinstance(result_block, dict):
            raise ParseError('missing lighthouseResult')

        cats = result_block.get('categories') or {}
        categories: dict[str, int | str] = {}
        scores: list[int] = []
        for cat_id in _CATEGORIES:
            cat_data = cats.get(cat_id)
            if not isinstance(cat_data, dict):
                categories[cat_id] = 'n/a'
                continue
            raw = cat_data.get('score')
            if raw is None:
                categories[cat_id] = 'n/a'
                continue
            value = round(float(raw) * 100)
            categories[cat_id] = value
            scores.append(value)

        overall_score = round(sum(scores) / len(scores)) if scores else 0
        fixes = _build_fixes(result_block)

        return ToolResult(
            tool=self.TOOL_NAME,
            target=target,
            status=Status.OK,
            score=overall_score,
            categories=categories,
            fixes=fixes,
        )


def _build_fixes(lighthouse: dict[str, Any]) -> tuple[Fix, ...]:
    """Top audits con weight>0 y score<1.0 ordenados por impacto."""
    audits = lighthouse.get('audits') or {}
    cats = lighthouse.get('categories') or {}
    weight_by_audit: dict[str, tuple[str, float]] = {}
    for cat_id, cat_data in cats.items():
        if not isinstance(cat_data, dict):
            continue
        for ref in cat_data.get('auditRefs') or []:
            if not isinstance(ref, dict):
                continue
            weight = float(ref.get('weight') or 0)
            audit_id = ref.get('id')
            if not isinstance(audit_id, str) or weight <= 0:
                continue
            prev_weight = weight_by_audit.get(audit_id, ('', 0.0))[1]
            if weight > prev_weight:
                weight_by_audit[audit_id] = (cat_id, weight)

    failing: list[tuple[str, dict[str, Any], str, float]] = []
    for audit_id, (cat_id, weight) in weight_by_audit.items():
        audit = audits.get(audit_id)
        if not isinstance(audit, dict):
            continue
        score = audit.get('score')
        if score is None or score >= 1.0:
            continue
        failing.append((audit_id, audit, cat_id, weight))

    failing.sort(key=lambda x: (-x[3], x[0]))
    fixes: list[Fix] = []
    for audit_id, audit, cat_id, weight in failing[:_TOP_FIXES]:
        title = audit.get('title') or audit_id
        description = audit.get('description') or ''
        fixes.append(
            Fix(
                severity=_severity_for_weight(weight),
                category=cat_id,
                issue=str(title),
                fix=str(description)[:300],
                reach=int(min(weight * 10, 10)),
            )
        )
    return tuple(fixes)


def _severity_for_weight(weight: float) -> Severity:
    if weight >= 5:
        return Severity.HIGH
    if weight >= 2:
        return Severity.MEDIUM
    return Severity.LOW


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
