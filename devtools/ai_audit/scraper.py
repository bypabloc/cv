"""Orquestador del ai_audit: corre todos los (target, tool) con
Playwright async, retry exp backoff y skip BLOCKED.

Sleeps entre tools y targets para no saturar servidores. Cada tool
es independiente: un fallo NUNCA aborta el run global.
"""

import asyncio
import subprocess
import time
from typing import Any

from ai_audit import auth
from ai_audit.tools import REGISTRY
from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Status
from ai_audit.tools.base import Tool
from ai_audit.tools.base import ToolResult


TARGET_SLEEP_SECONDS = 2.0
TOOL_SLEEP_SECONDS = 5.0
RETRY_WAITS_SECONDS: tuple[float, ...] = (5.0, 15.0, 45.0)
SCRAPE_TIMEOUT_SECONDS = 120.0


async def run_audit(
    *,
    targets: list[str],
    tool_names: list[str],
    headless: bool = True,
) -> list[ToolResult]:
    """Ejecuta el audit completo y devuelve resultados por (target, tool)."""
    # Import diferido: chromium se descarga en el primer run.
    from playwright.async_api import async_playwright

    results: list[ToolResult] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        try:
            for i, target in enumerate(targets):
                if i > 0:
                    await asyncio.sleep(TARGET_SLEEP_SECONDS)
                for j, tool_name in enumerate(tool_names):
                    if j > 0:
                        await asyncio.sleep(TOOL_SLEEP_SECONDS)
                    result = await _scrape_with_retry(
                        browser=browser,
                        tool_name=tool_name,
                        target=target,
                    )
                    results.append(result)
        finally:
            await browser.close()
    return results


async def _scrape_with_retry(
    *,
    browser: Any,
    tool_name: str,
    target: str,
) -> ToolResult:
    """Aplica retry exp backoff. Devuelve BLOCKED tras 3 fallos."""
    tool: Tool = REGISTRY[tool_name]

    if tool.REQUIRES_AUTH:
        state = auth.check(tool_name)
        if state != auth.AuthState.VALID:
            return _skipped_result(
                tool_name=tool_name,
                target=target,
                reason=f'storageState {state.value}',
            )

    storage_state = auth.load(tool_name) if tool.REQUIRES_AUTH else None
    context = await browser.new_context(storage_state=storage_state)
    page = await context.new_page()
    try:
        return await _try_with_backoff(
            tool=tool,
            page=page,
            target=target,
        )
    finally:
        await context.close()


async def _try_with_backoff(
    *,
    tool: Tool,
    page: Any,
    target: str,
) -> ToolResult:
    """Loop de retry: hasta 3 intentos con waits [5, 15, 45]s."""
    start = time.monotonic()
    last_error: str | None = None
    for attempt in range(len(RETRY_WAITS_SECONDS) + 1):
        if attempt > 0:
            await asyncio.sleep(RETRY_WAITS_SECONDS[attempt - 1])
        try:
            return await tool.scrape(page, target)
        except BlockedError as exc:
            last_error = f'BLOCKED: {exc}'
            continue
        except (ParseError, Exception) as exc:  # noqa: BLE001
            last_error = f'{type(exc).__name__}: {exc}'
            if attempt >= len(RETRY_WAITS_SECONDS):
                return _error_result(
                    tool_name=tool.TOOL_NAME,
                    target=target,
                    error=last_error,
                    start=start,
                )
            continue
    return _blocked_result(
        tool_name=tool.TOOL_NAME,
        target=target,
        reason=last_error or 'BLOCKED after 3 retries',
        start=start,
    )


def _skipped_result(
    *,
    tool_name: str,
    target: str,
    reason: str,
) -> ToolResult:
    return ToolResult(
        tool=tool_name,
        target=target,
        status=Status.SKIPPED,
        score=None,
        skipped_reason=reason,
    )


def _blocked_result(
    *,
    tool_name: str,
    target: str,
    reason: str,
    start: float,
) -> ToolResult:
    return ToolResult(
        tool=tool_name,
        target=target,
        status=Status.BLOCKED,
        score=None,
        duration_ms=int((time.monotonic() - start) * 1000),
        error_message=reason,
    )


def _error_result(
    *,
    tool_name: str,
    target: str,
    error: str,
    start: float,
) -> ToolResult:
    return ToolResult(
        tool=tool_name,
        target=target,
        status=Status.ERROR,
        score=None,
        duration_ms=int((time.monotonic() - start) * 1000),
        error_message=error,
    )


def resolve_exit_code(results: list[ToolResult]) -> int:
    """0 si >50% OK; 1 si >=50% BLOCKED/ERROR."""
    if not results:
        return 2
    bad = sum(1 for r in results if r.status in (Status.BLOCKED, Status.ERROR))
    if bad * 2 >= len(results):
        return 1
    return 0


def auto_install_chromium() -> None:
    """Instala chromium si no esta presente. Idempotente.

    Se invoca en el primer run para evitar fallo silencioso por
    binario faltante.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        msg = 'playwright no instalado. Correr: cd devtools && uv sync'
        raise RuntimeError(msg) from None
    # El check del binario lo hace Playwright al lanzar; aca corremos
    # `playwright install chromium` para garantizar que esta el binario.
    # Es idempotente: si ya esta, no descarga nada.
    subprocess.run(
        ['playwright', 'install', 'chromium'],  # noqa: S607
        check=True,
        capture_output=True,
        timeout=600,
    )
