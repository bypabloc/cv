"""Tool `validators`: fetchea recursos del target y los pasa por los puros.

Cubre 4 checks que NO entrega isitagentready (o que entrega como
neutral/parcial):

1. `llms.txt`        — spec llmstxt.org (size, formato, links).
2. `robots.txt`      — deteccion de AI bots bloqueados accidentalmente.
3. `sitemap.xml`     — presencia + shape XML + count de URLs.
4. JSON-LD Person    — schema.org Person/Organization en HTML del home.

Anonima (sin auth). Implementada con httpx puro (sin Playwright):
fetcha los 4 recursos en paralelo y suma los `pass`/`fail` en un score
de 0-100 (porcentaje de validators verdes).
"""

import asyncio
import time
from typing import Any

import httpx

from ai_audit import validators
from ai_audit.tools.base import Fix
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import ToolResult


_TIMEOUT_SECONDS = 30.0

_VALIDATOR_PATHS = (
    ('llms.txt', '/llms.txt', validators.validate_llms_txt),
    ('robots.txt', '/robots.txt', validators.validate_robots_ai_bots),
    ('sitemap.xml', '/sitemap.xml', validators.validate_sitemap_xml),
    ('json-ld', '', validators.validate_json_ld_person),
)


class Validators:
    """Tool: fetcha recursos del target y corre validadores OSS propios."""

    TOOL_NAME = 'validators'
    REQUIRES_AUTH = False
    BASE_URL = 'local'

    async def scrape(self, page: Any, target: str) -> ToolResult:
        """Fetcha los 4 recursos del target y corre los validators."""
        del page
        start = time.monotonic()
        try:
            results = await self._fetch_all(target)
        except httpx.HTTPError as exc:
            raise ParseError(f'http error: {exc}') from exc

        validation = self._run_validators(target, results)
        return _with_duration(validation, start)

    async def _fetch_all(
        self,
        target: str,
    ) -> dict[str, str | None]:
        """Fetcha llms.txt, robots.txt, sitemap.xml y home en paralelo.

        Si /sitemap.xml no devuelve XML valido (404 o HTML), prueba
        con /sitemap-index.xml (lo que Astro genera por default).
        """
        async with httpx.AsyncClient(
            timeout=_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (compatible; portfolio-ai-audit/1.0)'
                ),
            },
        ) as client:
            paths = ['/llms.txt', '/robots.txt', '/sitemap.xml', '']
            urls = [
                validators.normalize_url(target, p) if p else target
                for p in paths
            ]
            responses = await asyncio.gather(
                *[client.get(u) for u in urls],
                return_exceptions=True,
            )
            out: dict[str, str | None] = {}
            for path, response in zip(paths, responses, strict=True):
                key = path.lstrip('/') or 'home'
                if isinstance(response, Exception):
                    out[key] = None
                    continue
                if response.status_code != 200:
                    out[key] = None
                    continue
                out[key] = response.text

            # Fallback: si sitemap.xml ausente o NO empieza con XML,
            # probar /sitemap-index.xml (default Astro).
            if _needs_sitemap_fallback(out.get('sitemap.xml')):
                try:
                    fallback = await client.get(
                        validators.normalize_url(target, '/sitemap-index.xml'),
                    )
                    if (
                        fallback.status_code == 200
                        and fallback.text.lstrip().startswith(
                            ('<?xml', '<urlset', '<sitemapindex'),
                        )
                    ):
                        out['sitemap.xml'] = fallback.text
                except httpx.HTTPError:  # noqa: S110 - fallback best-effort
                    pass

        return out

    def _run_validators(
        self,
        target: str,
        fetched: dict[str, str | None],
    ) -> ToolResult:
        """Corre los 4 validators contra los recursos fetcheados."""
        per_check: dict[str, dict[str, Any]] = {
            'llms.txt': validators.validate_llms_txt(fetched.get('llms.txt')),
            'robots.txt': validators.validate_robots_ai_bots(
                fetched.get('robots.txt'),
            ),
            'sitemap.xml': validators.validate_sitemap_xml(
                fetched.get('sitemap.xml'),
            ),
            'json-ld': validators.validate_json_ld_person(
                fetched.get('home'),
            ),
        }

        # Score: pass=1.0, neutral=0.5, fail=0.0. Neutral cuenta como
        # medio credito porque es un estado intencional del owner
        # (ej. Cloudflare-managed robots) que NO penalizamos como fail.
        total = len(per_check)
        weighted = sum(_status_weight(v['status']) for v in per_check.values())
        score = round(weighted / total * 100) if total else 0

        categories: dict[str, int | str] = {
            name: round(_status_weight(v['status']) * 100)
            for name, v in per_check.items()
        }

        # Solo los `fail` generan Fix; `neutral` es intencional, sin
        # accion requerida.
        fixes = tuple(
            Fix(
                severity=_severity_for(name),
                category=name,
                issue=v['message'],
                fix=_fix_hint_for(name),
                reach=_reach_for(name),
            )
            for name, v in per_check.items()
            if v['status'] == 'fail'
        )

        return ToolResult(
            tool=self.TOOL_NAME,
            target=target,
            status=Status.OK,
            score=score,
            categories=categories,
            fixes=fixes,
        )


_SEVERITY_BY_CHECK = {
    'llms.txt': Severity.MEDIUM,
    'robots.txt': Severity.HIGH,
    'sitemap.xml': Severity.MEDIUM,
    'json-ld': Severity.HIGH,
}

_REACH_BY_CHECK = {
    'llms.txt': 4,
    'robots.txt': 8,
    'sitemap.xml': 4,
    'json-ld': 8,
}

_FIX_HINTS = {
    'llms.txt': (
        'Crear /llms.txt segun spec llmstxt.org: H1 con titulo + lista '
        'markdown de links a paginas clave del sitio.'
    ),
    'robots.txt': (
        'Revisar robots.txt: ningun AI bot conocido (GPTBot, ClaudeBot, '
        'PerplexityBot, etc.) deberia tener Disallow: / a menos que sea '
        'intencional.'
    ),
    'sitemap.xml': (
        'Servir /sitemap.xml (o sitemap-index.xml) con al menos una URL. '
        'En Astro: integration @astrojs/sitemap.'
    ),
    'json-ld': (
        'Agregar JSON-LD schema.org Person (CV) u Organization en el '
        'home: <script type="application/ld+json">{"@context":"...","@type":"Person",...}</script>'
    ),
}


def _needs_sitemap_fallback(content: str | None) -> bool:
    """True si /sitemap.xml no parece XML valido (404 o catch-all HTML).

    Astro genera por default `/sitemap-index.xml` y NO `/sitemap.xml`,
    asi que el endpoint canonico devuelve HTML del catch-all. Caemos
    al index si lo detectamos.
    """
    if not content:
        return True
    return not content.lstrip().startswith(
        ('<?xml', '<urlset', '<sitemapindex'),
    )


def _status_weight(status: str) -> float:
    """Pondera el status para el score: pass=1.0, neutral=0.5, fail=0.0."""
    if status == 'pass':
        return 1.0
    if status == 'neutral':
        return 0.5
    return 0.0


def _severity_for(check: str) -> Severity:
    return _SEVERITY_BY_CHECK.get(check, Severity.MEDIUM)


def _reach_for(check: str) -> int:
    return _REACH_BY_CHECK.get(check, 4)


def _fix_hint_for(check: str) -> str:
    return _FIX_HINTS.get(check, '')


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
