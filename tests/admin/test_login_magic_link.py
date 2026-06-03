"""Login del admin: form, link a registro, email no registrado, magic-link.

Porta `tests/feature/admin/01-login-magic-link.spec.ts` y AMPLIA al flujo
REAL end-to-end del magic-link (login.start -> seed -> verify-magic-link 302
-> shell autenticado). [AC-2]

El submit del form de login esta gateado por Turnstile, que en el build
DESPLEGADO de dev NO esta en modo E2E: el submit nunca se habilita en
headless sin resolver un challenge. Por eso el "email no registrado -> 404"
se valida en la capa que el admin sirve real (login.start del backend, que
es lo que el form invocaria), no forzando el submit. El render del form +
el link a registro SI se validan en el browser. El login REAL del usuario se
ejercita por el camino del magic-link (que el admin desplegado honra).
"""

from __future__ import annotations

from playwright.sync_api import Page

from .conftest import AdminAuth


def test_login_page_renders_form(page: Page, admin_url: str) -> None:
    """
    Given el admin desplegado,
    When abro /login,
    Then la page responde y muestra el heading + el input de email (testid).
    """
    # Arrange / Act
    response = page.goto(f'{admin_url}/login/', wait_until='load')

    # Assert
    assert response is not None
    assert response.status == 200
    page.wait_for_selector('text=Iniciar sesion', timeout=10_000)
    assert page.get_by_test_id('login-email').count() == 1


def test_login_page_links_to_register(page: Page, admin_url: str) -> None:
    """
    Given /login,
    When inspecciono el link "Registrate",
    Then su href apunta a /register.
    """
    # Arrange
    page.goto(f'{admin_url}/login/', wait_until='load')

    # Act
    href = page.get_by_role('link', name='Registrate').get_attribute('href')

    # Assert
    assert href == '/register/'


def test_login_start_unregistered_email_returns_404(auth: AdminAuth) -> None:
    """
    Given un email NO registrado,
    When el admin dispara login.start (lo que hace el submit del form),
    Then el backend dev responde 404 (EMAIL_NOT_FOUND, suggest_register).
    """
    # Arrange
    ghost = auth.new_email('ghost')

    # Act
    status = auth.login_start_status(ghost)

    # Assert
    assert status == 404


def test_login_via_magic_link_lands_in_shell(
    page: Page,
    auth: AdminAuth,
) -> None:
    """
    Given un user active y un magic-link de login seedeado en Neon,
    When el backend resuelve verify-magic-link (302) y el browser abre el
        callback que devuelve,
    Then el admin decodifica los tokens y aterriza en el shell autenticado.
    """
    # Arrange
    email, user_id, _access, _refresh = auth.create_active_user('login-ml')
    callback = auth.magic_link_callback_url(email, user_id)

    # Act
    page.goto(callback, wait_until='load')

    # Assert
    page.wait_for_selector('text=Panel de administracion', timeout=25_000)
    assert page.url == f'{auth.origin}/'
