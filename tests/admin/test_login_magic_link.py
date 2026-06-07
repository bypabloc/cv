"""Login del admin: form, fusion register, check-email, magic-link.

Login UNIFICADO (plan admin-security-overview, bloque D): la operation
`register` se fusiono en `login`. El primer paso del login es
`login.check-email` (existencia + has_password, sin exponer los metodos
MFA); un email no registrado YA NO da 404 ni hay un link "Registrate" a
`/register` — el registro ocurre dentro del propio login (login.start crea
el user si el email no existe). El login REAL del usuario se ejercita por el
camino del magic-link (que el admin desplegado honra). [AC-2]
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


def test_login_page_has_no_register_link(page: Page, admin_url: str) -> None:
    """
    Given /login (login unificado, fusion register->login),
    When inspecciono la page,
    Then NO existe un link "Registrate" a /register (el registro ocurre
        dentro del propio login).
    """
    # Arrange
    page.goto(f'{admin_url}/login/', wait_until='load')

    # Act / Assert
    assert page.get_by_role('link', name='Registrate').count() == 0


def test_check_email_unregistered_returns_not_exists(auth: AdminAuth) -> None:
    """
    Given un email NO registrado,
    When el admin dispara login.check-email (paso 1 del login),
    Then el backend dev responde {exists: false} (la UI ofrece crear cuenta);
        ya NO devuelve 404 (la fusion register->login crea la cuenta en
        login.start, no rechaza el email).
    """
    # Arrange
    ghost = auth.new_email('ghost')

    # Act
    body = auth.login_check_email(ghost)

    # Assert
    assert body['exists'] is False


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
