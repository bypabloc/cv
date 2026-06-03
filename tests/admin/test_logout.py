"""Logout del admin (UI real) + entrada al shell sin sesion + SPA fallback.

Porta `tests/feature/admin/05-logout-multi-tab.spec.ts` y AMPLIA al logout
REAL via la UI: estando logueado, abrir el menu de usuario y cerrar sesion
-> /login + tokens limpiados de localStorage. Tambien cubre el guard de la
entrada al shell (/) sin sesion y el SPA fallback de una ruta dinamica
inexistente. [AC-2]

El logout multi-tab (BroadcastChannel) se cubre a fondo en los unit tests del
admin (use-multi-tab-sync); aqui el flujo real de un solo tab.
"""

from __future__ import annotations

import json

from playwright.sync_api import Page

from .conftest import Flows


def test_logout_clears_session_and_redirects_to_login(
    logged_in_page: tuple[Page, str, str],
    flows: Flows,
) -> None:
    """
    Given una sesion activa en el shell,
    When abro el menu de usuario y hago click en "Cerrar sesion",
    Then el admin redirige a /login y limpia el refreshToken de localStorage.
    """
    # Arrange
    page = logged_in_page[0]

    # Act
    flows.logout(page)

    # Assert
    assert '/login' in page.url
    stored = page.evaluate(
        "() => localStorage.getItem('portfolio-admin-auth')",
    )
    parsed = json.loads(stored)
    assert parsed['state']['refreshToken'] is None


def test_shell_entry_without_session_redirects_to_login(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given sin sesion,
    When abro la raiz del shell (/),
    Then AuthGuard redirige a /login.
    """
    # Arrange / Act
    page.goto(f'{admin_url}/', wait_until='load')
    page.wait_for_url('**/login**', timeout=15_000)

    # Assert
    assert '/login' in page.url


def test_spa_fallback_serves_dynamic_route(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given una ruta dinamica inexistente del SPA,
    When la abro (/users/?user=usr_inexistente),
    Then el fallback (_redirects /* /index.html 200) sirve la app (2xx).
    """
    # Arrange / Act
    response = page.goto(
        f'{admin_url}/users/?user=usr_inexistente', wait_until='load',
    )

    # Assert
    assert response is not None
    assert response.status == 200
