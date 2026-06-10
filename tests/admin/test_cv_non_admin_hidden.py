"""Gestion CV oculta para un user NO whitelisted (anti-enumeration). [AC-13]

Doc 12 (`test_cv_non_admin_hidden`): con un user sintetico activo que NO
esta en la whitelist SSM `admin-emails`, el sidebar NO muestra el item
"Gestion CV" (adminOnly) y el acceso DIRECTO a /cv y /cv/experiences
muestra la pantalla de no autorizado (mismo tratamiento que users-admin
ante el 404: NI redirect a login NI crash).

Desvios del doc 12 anotados:
- Los items del sidebar NO tienen data-testid propio: el assert es por
  label dentro del `nav` del shell.
- El probe de rol (users.admin.list-users) responde el 404 ESPERADO de
  anti-enumeration: el browser SIEMPRE loguea ese fallo de red como
  console.error, por eso la captura lo filtra explicitamente (cualquier
  otro error de consola sigue fallando el spec).
"""

from __future__ import annotations

from playwright.sync_api import Page

from ._cv_ui import settle_network
from .conftest import AdminAuth
from .conftest import attach_console_capture


_UNAUTHORIZED_TEXT = 'No tienes acceso a esta seccion'
_LOAD_TIMEOUT = 25_000


def test_cv_non_admin_hidden(
    page: Page,
    auth: AdminAuth,
) -> None:
    """
    Given un user sintetico activo NO whitelisted autenticado en el shell,
    When mira el sidebar y navega DIRECTO a /cv y /cv/experiences,
    Then el item "Gestion CV" no existe en el nav y ambas rutas muestran
        la pantalla de no autorizado sin redirect a /login ni crash, con
        cero errores de consola (filtrado SOLO el 404 esperado del probe).
    """
    # Arrange: user normal (NO whitelisted) + captura de consola que
    # ignora el 404 esperado del probe de rol admin.
    console_errors = attach_console_capture(
        page,
        ignore_substrings=('the server responded with a status of 404',),
    )
    email, user_id, access, refresh = auth.create_active_user('noncvadmin')
    url = auth.callback_url(
        access=access,
        refresh=refresh,
        user_id=user_id,
        email=email,
    )
    page.goto(url, wait_until='load')
    page.wait_for_selector(
        'text=Panel de administracion',
        timeout=_LOAD_TIMEOUT,
    )

    # El sidebar ya resolvio el rol cuando renderiza sus items visibles.
    nav = page.locator('nav')
    nav.get_by_role('link', name='Metricas').wait_for(
        state='visible',
        timeout=_LOAD_TIMEOUT,
    )
    settle_network(page)

    # Assert: el item adminOnly "Gestion CV" NO existe para el no-admin.
    assert nav.get_by_role('link', name='Gestion CV').count() == 0

    # Act + Assert: /cv directo -> pantalla de no autorizado, sin redirect.
    page.goto(f'{auth.origin}/cv/', wait_until='load')
    page.wait_for_selector(
        f'text={_UNAUTHORIZED_TEXT}',
        timeout=_LOAD_TIMEOUT,
    )
    assert ('/cv/' in page.url) is True
    assert ('/login' in page.url) is False

    # Act + Assert: /cv/experiences directo -> idem.
    page.goto(f'{auth.origin}/cv/experiences/', wait_until='load')
    page.wait_for_selector(
        f'text={_UNAUTHORIZED_TEXT}',
        timeout=_LOAD_TIMEOUT,
    )
    assert ('/cv/experiences/' in page.url) is True
    assert ('/login' in page.url) is False

    # Cero errores de consola (mas alla del 404 esperado del probe).
    assert console_errors == []
