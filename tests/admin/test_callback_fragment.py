"""Callback del magic-link: redirects client-side sin tokens validos.

Porta `tests/feature/admin/03-callback-fragment-hash.spec.ts`. El callback
decodifica el fragment hash; sin fragment o con uno invalido redirige a
/login (logica 100% client-side, no toca el backend). [AC-2]

El camino feliz del callback (fragment valido -> shell) se cubre en
test_login_magic_link / test_register_verify (que llegan al shell por esta
misma ruta con tokens reales); aqui se cubren los casos de fragment ausente
e invalido.
"""

from __future__ import annotations

from playwright.sync_api import Page


def test_callback_without_fragment_redirects_to_login(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given /callback SIN fragment hash,
    When la page carga,
    Then el admin no encuentra tokens y redirige a /login (client-side).
    """
    # Arrange / Act
    page.goto(f'{admin_url}/callback/', wait_until='load')
    page.wait_for_url('**/login**', timeout=15_000)

    # Assert
    assert '/login' in page.url


def test_callback_with_invalid_fragment_redirects_to_login(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given /callback con un fragment invalido (access/refresh vacios),
    When la page carga,
    Then el admin no rompe y redirige a /login.
    """
    # Arrange / Act
    page.goto(f'{admin_url}/callback/#access=&refresh=', wait_until='load')
    page.wait_for_url('**/login**', timeout=15_000)

    # Assert
    assert '/login' in page.url
