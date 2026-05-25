"""Auth: Playwright storageState para tools que requieren login.

Las 2 tools con auth (Ahrefs, Semrush) requieren cuenta gratis. El
storageState (cookies + localStorage) se guarda en
``docker/env/dev-cli/ai-audit/<tool>.json`` (categoria dev-cli,
LOCAL-ONLY, gitignored).

Las otras 2 tools (isitagentready, aibotchecker) son anonimas y NO
usan este modulo.
"""

import asyncio
from enum import StrEnum
import json
from pathlib import Path
import stat

from shared.paths import PROJECT_ROOT


STORAGE_DIR = PROJECT_ROOT / 'docker' / 'env' / 'dev-cli' / 'ai-audit'

LOGIN_URLS: dict[str, str] = {
    'ahrefs': 'https://app.ahrefs.com/login',
    'semrush': 'https://www.semrush.com/login/',
}


class AuthState(StrEnum):
    """Estado del storageState para una tool."""

    VALID = 'VALID'
    EXPIRED = 'EXPIRED'
    MISSING = 'MISSING'


def storage_path(tool_name: str) -> Path:
    """Path absoluto al storageState de una tool."""
    return STORAGE_DIR / f'{tool_name}.json'


def load(tool_name: str) -> dict | None:
    """Carga el storageState. Retorna None si no existe.

    NO valida shape ni cookies expiradas — para eso usar ``check``.
    """
    path = storage_path(tool_name)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def save(tool_name: str, state: dict) -> None:
    """Persiste el storageState con perms 0600 (dir 0700)."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.chmod(stat.S_IRWXU)
    path = storage_path(tool_name)
    path.write_text(json.dumps(state), encoding='utf-8')
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def check(tool_name: str) -> AuthState:
    """Verifica shape del storageState sin abrir browser ni red."""
    path = storage_path(tool_name)
    if not path.exists():
        return AuthState.MISSING
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return AuthState.EXPIRED
    if not isinstance(data, dict):
        return AuthState.EXPIRED
    cookies = data.get('cookies')
    if not isinstance(cookies, list) or len(cookies) == 0:
        return AuthState.EXPIRED
    return AuthState.VALID


async def setup_interactive(tool_name: str, login_url: str) -> None:
    """Abre browser NO-headless, espera login manual, guarda state.

    Flujo:
    1. Abre Chromium con la URL de login del tool.
    2. Le pide al usuario loguearse y volver a la terminal.
    3. Cuando el usuario presiona Enter, captura cookies + storage y
       las persiste en ``storage_path(tool_name)``.

    NO se loggea el contenido del state (es credencial).
    """
    # Import diferido: playwright se descarga chromium en el primer run.
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(login_url, wait_until='domcontentloaded')
            print(
                f'\n[ai_audit] Browser abierto en {login_url}.\n'
                f'[ai_audit] Loguearse a {tool_name.upper()}, esperar al '
                f'dashboard, y volver aca.\n'
                f'[ai_audit] Cuando estes logueado, presiona ENTER '
                f'(NO cierres el browser todavia)...'
            )
            await _await_user_enter()
            await context.storage_state(path=str(storage_path(tool_name)))
            # Reapply perms (storage_state escribe con 0644 por default)
            storage_path(tool_name).chmod(stat.S_IRUSR | stat.S_IWUSR)
            print(
                f'[ai_audit] storageState guardado en '
                f'{storage_path(tool_name)}',
            )
        finally:
            await browser.close()


async def _await_user_enter() -> None:
    """Espera Enter del usuario sin bloquear el event loop."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, input)
