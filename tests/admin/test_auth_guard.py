"""AuthGuard del admin: rutas protegidas sin sesion -> /login?next=<path>.

Porta `tests/feature/admin/04-auth-guard-redirect.spec.ts`. Cada ruta del
area protegida, abierta sin sesion, redirige a /login con el `next` que
codifica la ruta original. [AC-2]
"""

from __future__ import annotations

import urllib.parse

from playwright.sync_api import Page


def test_settings_without_session_redirects_to_login_with_next(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given sin sesion,
    When accedo a /settings,
    Then AuthGuard redirige a /login con next=/settings.
    """
    # Arrange / Act
    page.goto(f'{admin_url}/settings/', wait_until='load')
    page.wait_for_url('**/login/?next=*', timeout=15_000)

    # Assert
    assert 'next=' in page.url
    assert '/settings' in urllib.parse.unquote(page.url)


def test_sessions_without_session_redirects_to_login_with_next(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given sin sesion,
    When accedo a /sessions,
    Then AuthGuard redirige a /login con next=/sessions.
    """
    # Arrange / Act
    page.goto(f'{admin_url}/sessions/', wait_until='load')
    page.wait_for_url('**/login/?next=*', timeout=15_000)

    # Assert
    assert 'next=' in page.url
    assert '/sessions' in urllib.parse.unquote(page.url)


def test_users_without_session_redirects_to_login_with_next(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given sin sesion,
    When accedo a /users,
    Then AuthGuard redirige a /login con next=/users.
    """
    # Arrange / Act
    page.goto(f'{admin_url}/users/', wait_until='load')
    page.wait_for_url('**/login/?next=*', timeout=15_000)

    # Assert
    assert 'next=' in page.url
    assert '/users' in urllib.parse.unquote(page.url)
