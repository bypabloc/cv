"""Auth: stub para tools que NO requieren storageState.

Historicamente este modulo soportaba Ahrefs y Semrush (login
interactivo + cookies en Playwright storageState). Esas tools fueron
descartadas en mayo 2026 cuando se confirmó que sus APIs cuestan
$500+/mes y no hay free tier.

Las tools activas hoy (isitagentready, validators, lighthouse_psi) son
todas anonimas o usan API key gratuita resuelta directamente por la
tool desde docker/env/dev-cli/.{env} (ver `tools/lighthouse_psi.py`).

Este modulo se conserva solo como compat con scraper.py — todos los
helpers reportan estado seguro cuando ninguna tool necesita auth.
"""

from enum import StrEnum
from pathlib import Path

from shared.paths import PROJECT_ROOT


STORAGE_DIR = PROJECT_ROOT / 'docker' / 'env' / 'dev-cli' / 'ai-audit'

# Dict vacio: ninguna tool activa requiere storageState.
LOGIN_URLS: dict[str, str] = {}


class AuthState(StrEnum):
    """Estado del storageState para una tool."""

    VALID = 'VALID'
    EXPIRED = 'EXPIRED'
    MISSING = 'MISSING'


def storage_path(tool_name: str) -> Path:
    """Path absoluto al storageState de una tool (compat)."""
    return STORAGE_DIR / f'{tool_name}.json'


def load(tool_name: str) -> dict | None:
    """Compat: ninguna tool activa usa storageState. Siempre None."""
    del tool_name
    return None


def check(tool_name: str) -> AuthState:
    """Compat: ninguna tool activa usa storageState. Siempre VALID."""
    del tool_name
    return AuthState.VALID
