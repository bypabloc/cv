"""Settings del admin: guard sin sesion + update REAL del display_name.

Porta `tests/feature/admin/06-settings-profile-update.spec.ts` y AMPLIA al
flujo REAL: estando logueado, editar el display_name en /settings -> el
backend (users.profile.update) lo persiste -> se verifica server-side. [AC-2]

NOTA del DOM: el ProfileForm del admin hace `reset()` del campo cada vez que
cambia la referencia de `profile.data`. Con un user recien creado el
display_name arranca vacio (undefined) -> el efecto entra en un loop que
borra cualquier valor que se escriba. Se evita seedeando un display_name
ESTABLE via API ANTES de abrir el form: con un valor no vacio el efecto deja
de re-disparar y el campo es editable. (El loop con campo vacio es un detalle
del componente, cubierto por sus unit tests; aqui se ejercita el update real.)
"""

from __future__ import annotations

import secrets
import urllib.parse

from playwright.sync_api import Page

from .conftest import AdminAuth
from .conftest import Flows


def test_settings_without_session_redirects_to_login(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given sin sesion,
    When abro /settings,
    Then AuthGuard redirige a /login con next=/settings.
    """
    # Arrange / Act
    page.goto(f'{admin_url}/settings/', wait_until='load')
    page.wait_for_url('**/login/?next=*', timeout=15_000)

    # Assert
    assert '/settings' in urllib.parse.unquote(page.url)


def test_settings_security_route_serves_via_spa_fallback(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given el build estatico del admin,
    When abro /settings/security,
    Then el SPA fallback sirve la app (2xx) — la ruta existe en el build.
    """
    # Arrange / Act
    response = page.goto(f'{admin_url}/settings/security/', wait_until='load')

    # Assert
    assert response is not None
    assert response.status == 200


def test_settings_update_display_name_persists_server_side(
    logged_in_page: tuple[Page, str, str],
    auth: AdminAuth,
    flows: Flows,
) -> None:
    """
    Given una sesion activa con un display_name inicial estable,
    When edito el display_name en /settings y guardo,
    Then aparece el toast de exito y el backend persiste el nuevo valor
        (verificado via users.profile.get).
    """
    # Arrange: el browser ya esta en el shell. Para las operaciones de API uso
    # una sesion API NUEVA del mismo user (familia propia): el bootstrap del
    # admin rota SU familia y blacklistea su access, por eso NO reuso el token
    # del callback. Seedeo un display_name estable (el ProfileForm entra en un
    # loop de reset() si el campo arranca vacio).
    page = logged_in_page[0]
    email, user_id = logged_in_page[1], logged_in_page[2]
    api_access = auth.fresh_login(email, user_id)
    assert auth.update_display_name(api_access, 'Initial Name') == 200
    new_name = f'E2E {secrets.token_hex(3)}'

    # Act: navego a settings via sidebar (preserva la sesion en memoria),
    # espero a que el form cargue el valor estable, lo reemplazo y guardo.
    flows.nav_via_sidebar(page, 'Configuracion', '**/settings/**')
    page.wait_for_function(
        "() => {const e = document.querySelector('input[name=display_name]'); "
        'return e && e.value.length > 0}',
        timeout=15_000,
    )
    name_input = page.get_by_label('Nombre para mostrar')
    name_input.fill(new_name)
    page.get_by_role('button', name='Guardar cambios').click()
    page.wait_for_selector('text=Perfil actualizado', timeout=12_000)

    # Assert: el backend devuelve el nuevo display_name (persistio de verdad).
    # Se verifica con un token de API NUEVO (familia propia, siempre valido).
    assert auth.server_display_name(auth.fresh_login(email, user_id)) == new_name
