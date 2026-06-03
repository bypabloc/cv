"""TrackingPixel always-on en las 6 apps + sin consent + re-trigger (AC-3).

Porta `tests/feature/tracking/track-pageload.spec.ts`:
  - cada subdominio emite `POST /track` (page_load) al cargar SIN opt-in.
  - NO existe banner de consentimiento ni boton "Gestionar consentimiento".
  - una segunda navegacion en la misma sesion re-dispara un page_load nuevo
    (mismo session_id, event_id distinto, page_url nueva).

El pixel envia por `navigator.sendBeacon`; el test lo neutraliza
(`disable_send_beacon`) para que caiga al `fetch` legible. SIEMPRE
intercepta `POST /track` con `capture_track` (responde 204 local): NUNCA
deja salir el request real -> no muta el backend desplegado.

Desviacion vs el spec TS: la navegacion SPA usaba `window.navigate('/about')`
(ClientRouter), que NO esta expuesto en el deploy de Cloudflare Pages
(`typeof window.navigate === 'undefined'`), y `/about` redirige 308 a la
canonica `/about/`. Se navega con `page.goto('/about/')` (full load a la
canonica): exercita el mismo comportamiento observable (segunda carga ->
page_load nuevo con page_url distinta y event_id propio).
"""

from __future__ import annotations

from collections.abc import Callable
import re

from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools
from shared.browser import TrackCapturer


# UUID con o sin guiones (event_id viaja sin guiones en el payload).
_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?'
    r'[0-9a-f]{4}-?[0-9a-f]{12}$',
    re.IGNORECASE,
)
_PAGE_LOAD_TYPE = '019e372b-e0a7-7154-8279-8829bcf6a08c'

_NICHES = ('generic', 'hub', 'fintech', 'architect', 'leader', 'vibe')

# 20s en steps de 200ms: cubre el cold start del primer load de la sesion.
_POLL_STEPS = 100
_POLL_INTERVAL_MS = 200


def _wait_count(page: Page, capturer: TrackCapturer, minimum: int) -> bool:
    """Poll hasta que el capturer tenga >= `minimum` payloads.

    Usa `page.wait_for_timeout` (NO `time.sleep`): solo `wait_for_timeout`
    bombea el event loop sync de Playwright, dejando que el handler de
    `page.route('**/track')` corra y agregue el payload al capturer. Un
    `time.sleep` puro bloquea sin procesar la request interceptada.
    """
    for _ in range(_POLL_STEPS):
        if capturer.count >= minimum:
            return True
        page.wait_for_timeout(_POLL_INTERVAL_MS)
    return capturer.count >= minimum


@pytest.mark.app
@pytest.mark.parametrize('niche', _NICHES)
def test_tracking_pageload_emits_track_without_optin(
    page: Page,
    subdomain: Callable[[str], str],
    niche: str,
) -> None:
    """Cada subdominio emite page_load al cargar sin opt-in previo.

    Given el niche `{niche}` con `/track` interceptado y sendBeacon off,
    When se carga su home `/`,
    Then se captura un payload con el event_type_id de page_load, un event_id
    con forma UUID, un session_id de >= 20 chars y una page_url del origin
    del niche.
    """
    # Arrange
    browser_tools.disable_send_beacon(page)
    capturer = browser_tools.capture_track(page)
    origin = subdomain(niche)

    # Act
    browser_tools.goto(page, f'{origin}/')
    captured = _wait_count(page, capturer, 1)

    # Assert
    assert captured is True
    payload = capturer.payloads[0]
    assert payload['event_type_id'] == _PAGE_LOAD_TYPE
    assert _UUID_RE.match(str(payload['event_id'])) is not None
    assert len(str(payload['session_id'])) >= 20
    assert origin in str(payload['page_url'])


@pytest.mark.app
def test_tracking_pageload_no_consent_banner_present(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """No hay banner ni boton de consentimiento (tracking always-on).

    Given el apex cargado,
    When se inspecciona el DOM,
    Then no existe ningun dialog de consentimiento (ES/EN), ni el boton
    `manage-consent`, ni el `#cookie-banner`.
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("generic")}/')

    # Act
    dialog_count = page.get_by_role(
        'dialog',
        name=re.compile(
            r'Consentimiento de analytics|Analytics consent',
            re.IGNORECASE,
        ),
    ).count()
    manage_count = page.locator('[data-testid="manage-consent"]').count()
    banner_count = page.locator('#cookie-banner').count()

    # Assert
    assert dialog_count == 0
    assert manage_count == 0
    assert banner_count == 0


@pytest.mark.app
def test_tracking_pageload_two_loads_share_session_distinct_event(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Dos cargas en la misma sesion comparten session_id, no el event_id.

    Given el apex con `/track` interceptado,
    When se cargan dos paginas (`/` y `/about/`) en la misma sesion del
    browser,
    Then el primer y segundo payload comparten session_id pero tienen
    event_id distinto.
    """
    # Arrange
    browser_tools.disable_send_beacon(page)
    capturer = browser_tools.capture_track(page)
    base = subdomain('generic')

    # Act
    browser_tools.goto(page, f'{base}/')
    assert _wait_count(page, capturer, 1) is True
    browser_tools.goto(page, f'{base}/about/')
    assert _wait_count(page, capturer, 2) is True

    # Assert
    assert (
        capturer.payloads[0]['session_id']
        == (capturer.payloads[1]['session_id'])
    )
    assert (
        capturer.payloads[0]['event_id'] != (capturer.payloads[1]['event_id'])
    )


@pytest.mark.app
def test_tracking_pageload_second_navigation_retriggers_with_new_url(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Navegar de `/` a `/about/` re-dispara un page_load con page_url nueva.

    Given el apex cargado y su page_load capturado,
    When se navega a `/about/`,
    Then se captura un evento cuya page_url contiene `/about` y cuyo event_id
    difiere del primero.
    """
    # Arrange
    browser_tools.disable_send_beacon(page)
    capturer = browser_tools.capture_track(page)
    base = subdomain('generic')

    # Act
    browser_tools.goto(page, f'{base}/')
    assert _wait_count(page, capturer, 1) is True
    first_event_id = capturer.payloads[0]['event_id']
    browser_tools.goto(page, f'{base}/about/')

    about_event = None
    for _ in range(_POLL_STEPS):
        about_event = next(
            (
                p
                for p in capturer.payloads
                if '/about' in str(p.get('page_url', ''))
            ),
            None,
        )
        if about_event is not None:
            break
        page.wait_for_timeout(_POLL_INTERVAL_MS)

    # Assert
    assert about_event is not None
    assert '/about' in str(about_event['page_url'])
    assert about_event['event_id'] != first_event_id
