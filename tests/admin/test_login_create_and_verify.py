"""Alta + verify del admin: /verify + login.start (alta) + verify-code real.

Login UNIFICADO: el alta ocurre dentro del propio login (`login.start` crea el
user si el email no existe; la operation `register` fue eliminada). Por eso ya
NO hay una page `/register`. Lo que se valida aqui: la page `/verify` (input
del code) + el flujo de alta + verify REAL por backend (`login.check-email` ->
`login.start` (alta) -> `login.verify-code`), aterrizando la sesion en el shell
via callback.
"""

from __future__ import annotations

from playwright.sync_api import Page

from .conftest import AdminAuth


def test_verify_page_renders_heading(page: Page, admin_url: str) -> None:
    """
    Given /verify?flow=login,
    When abro la page,
    Then responde y muestra el heading "Verifica tu email".
    """
    # Arrange / Act
    response = page.goto(
        f'{admin_url}/verify/?flow=login', wait_until='load',
    )

    # Assert
    assert response is not None
    assert response.status == 200
    page.wait_for_selector('text=Verifica tu email', timeout=10_000)


def test_login_verify_code_creates_active_session(auth: AdminAuth) -> None:
    """
    Given un email nuevo,
    When el admin dispara login.start (alta) + (con el code seedeado)
        login.verify-code,
    Then el backend emite access + refresh tokens reales para el user active.
    """
    # Arrange / Act
    email, user_id, access, refresh = auth.create_active_user('login-verify')

    # Assert
    assert email in auth.created_emails
    assert isinstance(user_id, str)
    assert len(user_id) == 36
    assert access is not None
    assert access.count('.') == 2
    assert refresh is not None
    assert refresh.count('.') == 2


def test_login_then_callback_lands_in_shell(
    page: Page,
    auth: AdminAuth,
) -> None:
    """
    Given los tokens reales de un alta + verify-code recien hecho,
    When el browser abre el callback con esos tokens en el fragment,
    Then el admin los persiste y aterriza en el shell autenticado.
    """
    # Arrange
    email, user_id, access, refresh = auth.create_active_user('login-shell')
    callback = auth.callback_url(
        access=access, refresh=refresh, user_id=user_id, email=email,
    )

    # Act
    page.goto(callback, wait_until='load')

    # Assert
    page.wait_for_selector('text=Panel de administracion', timeout=25_000)
    assert page.url == f'{auth.origin}/'
