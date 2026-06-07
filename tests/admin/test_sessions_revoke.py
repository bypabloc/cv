"""Sessions-mgmt del admin: guard sin sesion + revoke REAL de una sesion.

Porta `tests/feature/admin/07-sessions-mgmt-revoke.spec.ts` y AMPLIA al
flujo REAL: logueado con 2 sesiones (la 2da abierta via API), revocar una en
/sessions -> la fila desaparece de la tabla y la sesion se borra en Neon.
[AC-2]

NO confundir con la feature `sessions` de metricas (tracking de visitantes),
que vive en el plan b-analytics-api.
"""

from __future__ import annotations

import time
import urllib.parse

from playwright.sync_api import Page

from .conftest import AdminAuth
from .conftest import Flows


def test_sessions_without_session_redirects_to_login(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given sin sesion,
    When abro /settings/sessions (la tab "Sesiones" de Configuracion),
    Then AuthGuard redirige a /login con next=/settings/sessions.

    La gestion de sesiones se movio de /sessions a /settings/sessions (tab
    dentro de Configuracion) con el redisno del bloque admin-security.
    """
    # Arrange / Act
    page.goto(f'{admin_url}/settings/sessions/', wait_until='load')
    page.wait_for_url('**/login/?next=*', timeout=15_000)

    # Assert
    assert '/settings/sessions' in urllib.parse.unquote(page.url)


def test_cv_placeholder_route_serves_via_spa_fallback(
    page: Page,
    admin_url: str,
) -> None:
    """
    Given el build estatico del admin,
    When abro /cv (placeholder dentro del shell),
    Then el SPA fallback sirve la app (2xx).
    """
    # Arrange / Act
    response = page.goto(f'{admin_url}/cv/', wait_until='load')

    # Assert
    assert response is not None
    assert response.status == 200


def test_sessions_revoke_removes_one_session(
    logged_in_page: tuple[Page, str, str],
    auth: AdminAuth,
    environment,
    flows: Flows,
) -> None:
    """
    Given una sesion activa en el browser + una 2da sesion abierta via API,
    When abro la tab "Sesiones" de Configuracion y revoco la sesion NO-actual,
    Then la fila desaparece de la tabla (queda 1) y Neon registra 1 sesion.

    La gestion de sesiones se movio de /sessions a la tab "Sesiones" dentro de
    /settings (Configuracion). Una de las 2 sesiones es la del browser
    (is_current -> su boton Revocar esta deshabilitado); se revoca la OTRA (la
    de open_second_session), cuyo boton SI esta habilitado.
    """
    # Arrange: 2da sesion del MISMO user via API (login.verify-code).
    page, email, user_id = (
        logged_in_page[0], logged_in_page[1], logged_in_page[2]
    )
    auth.open_second_session(email, user_id)
    # El INSERT de la sesion en Neon es best-effort/async: dar margen.
    time.sleep(2)
    assert len(environment.session_ids(user_id)) == 2

    # Act: navego a Configuracion via sidebar (preserva la sesion en memoria),
    # entro a la tab Sesiones, espero 2 botones Revocar (1 disabled = la actual,
    # 1 habilitado = la otra) y revoco el habilitado.
    flows.nav_via_sidebar(page, 'Configuracion', '**/settings/**')
    page.get_by_role('link', name='Sesiones').click()
    page.wait_for_url('**/settings/sessions/**', timeout=15_000)
    page.wait_for_function(
        "() => [...document.querySelectorAll('button')]"
        ".filter(b => b.textContent.includes('Revocar')).length === 2",
        timeout=15_000,
    )
    enabled_revoke = page.get_by_role('button', name='Revocar').and_(
        page.locator('button:not([disabled])'),
    )
    enabled_revoke.first.click()

    # Assert: Neon deja 1 sesion (la del browser, no revocable). La tabla baja a
    # 1 fila tras la invalidacion de la lista.
    page.wait_for_function(
        "() => [...document.querySelectorAll('button')]"
        ".filter(b => b.textContent.includes('Revocar')).length === 1",
        timeout=15_000,
    )
    time.sleep(1)
    assert len(environment.session_ids(user_id)) == 1
