"""Register del admin: render del form, /verify, register+verify-code real.

Porta `tests/feature/admin/02-register-verify-code.spec.ts` y AMPLIA al
flujo REAL end-to-end: register.start -> seed del code en Neon ->
register.verify-code -> tokens reales -> el browser aterriza en el shell por
el callback. [AC-2]

El submit del form de register esta gateado por Turnstile (build desplegado
NO en modo E2E). El render del form + el /verify se validan en el browser; el
register+verify REAL se ejercita por backend (lo que el submit invocaria) y
la sesion resultante se aterriza en el shell via callback.
"""

from __future__ import annotations

from playwright.sync_api import Page

from .conftest import AdminAuth


def test_register_page_renders_form(page: Page, admin_url: str) -> None:
    """
    Given el admin desplegado,
    When abro /register,
    Then responde y muestra el input de email (testid register-email).
    """
    # Arrange / Act
    response = page.goto(f'{admin_url}/register/', wait_until='load')

    # Assert
    assert response is not None
    assert response.status == 200
    assert page.get_by_test_id('register-email').count() == 1


def test_verify_page_renders_heading(page: Page, admin_url: str) -> None:
    """
    Given /verify?flow=register,
    When abro la page,
    Then responde y muestra el heading "Verifica tu email".
    """
    # Arrange / Act
    response = page.goto(
        f'{admin_url}/verify/?flow=register', wait_until='load',
    )

    # Assert
    assert response is not None
    assert response.status == 200
    page.wait_for_selector('text=Verifica tu email', timeout=10_000)


def test_register_verify_code_creates_active_session(auth: AdminAuth) -> None:
    """
    Given un email nuevo,
    When el admin dispara register.start + (con el code seedeado)
        register.verify-code,
    Then el backend emite access + refresh tokens reales para el user active.
    """
    # Arrange / Act
    email, user_id, access, refresh = auth.create_active_user('reg-verify')

    # Assert
    assert email in auth.created_emails
    assert isinstance(user_id, str)
    assert len(user_id) == 36
    assert access is not None
    assert access.count('.') == 2
    assert refresh is not None
    assert refresh.count('.') == 2


def test_register_then_callback_lands_in_shell(
    page: Page,
    auth: AdminAuth,
) -> None:
    """
    Given los tokens reales de un register+verify-code recien hecho,
    When el browser abre el callback con esos tokens en el fragment,
    Then el admin los persiste y aterriza en el shell autenticado.
    """
    # Arrange
    email, user_id, access, refresh = auth.create_active_user('reg-shell')
    callback = auth.callback_url(
        access=access, refresh=refresh, user_id=user_id, email=email,
    )

    # Act
    page.goto(callback, wait_until='load')

    # Assert
    page.wait_for_selector('text=Panel de administracion', timeout=25_000)
    assert page.url == f'{auth.origin}/'
