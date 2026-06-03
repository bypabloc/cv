"""TrackingPixel payload: campos required, utm, viewport (AC-3).

Porta `tests/feature/tracking/track-payload-fields.spec.ts`: el contrato del
`POST /track`:
  - sin utm en la URL, el payload trae los campos required y los `utm_*`
    vacios (`''`, nunca undefined/null).
  - con `utm_source`/`utm_medium` en la URL, se parsean poblados; los demas
    quedan `''`.
  - el viewport refleja el `window.innerWidth/Height` real.

SIEMPRE intercepta `POST /track` con `capture_track` (responde 204 local):
NUNCA deja salir el request real -> no muta el backend desplegado.
"""

from __future__ import annotations

from collections.abc import Callable

from playwright.sync_api import Browser
from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools
from shared.browser import TrackCapturer


# 20s en steps de 200ms: cubre el cold start del primer load de la sesion.
_POLL_STEPS = 100
_POLL_INTERVAL_MS = 200


def _wait_first(page: Page, capturer: TrackCapturer) -> bool:
    """Poll hasta que haya al menos un payload capturado.

    Usa `page.wait_for_timeout` (NO `time.sleep`): solo `wait_for_timeout`
    bombea el event loop sync de Playwright, dejando que el handler de
    `page.route('**/track')` corra y agregue el payload al capturer.
    """
    for _ in range(_POLL_STEPS):
        if capturer.count >= 1:
            return True
        page.wait_for_timeout(_POLL_INTERVAL_MS)
    return capturer.count >= 1


@pytest.mark.app
def test_tracking_payload_without_utm_has_required_fields_empty_utm(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Sin utm: el payload trae los required y los `utm_*` vacios.

    Given el apex con `/track` interceptado y sin query utm,
    When se carga `/`,
    Then `page_path` es `/`, `page_title` y `referrer` son strings, y los
    cuatro `utm_*` son `''`.
    """
    # Arrange
    browser_tools.disable_send_beacon(page)
    capturer = browser_tools.capture_track(page)

    # Act
    browser_tools.goto(page, f'{subdomain("generic")}/')
    assert _wait_first(page, capturer) is True
    payload = capturer.payloads[0]

    # Assert
    assert '/' in str(payload['page_url'])
    assert payload['page_path'] == '/'
    assert isinstance(payload['page_title'], str)
    assert isinstance(payload['referrer'], str)
    assert payload['utm_source'] == ''
    assert payload['utm_medium'] == ''
    assert payload['utm_campaign'] == ''
    assert payload['utm_content'] == ''


@pytest.mark.app
def test_tracking_payload_with_utm_query_populates_those_fields(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Con utm en la URL: `utm_source`/`utm_medium` poblados, el resto vacio.

    Given el apex con `/track` interceptado,
    When se carga `/?utm_source=playwright&utm_medium=e2e`,
    Then `utm_source` es `playwright`, `utm_medium` es `e2e` y
    `utm_campaign`/`utm_content` quedan `''`.
    """
    # Arrange
    browser_tools.disable_send_beacon(page)
    capturer = browser_tools.capture_track(page)
    url = f'{subdomain("generic")}/?utm_source=playwright&utm_medium=e2e'

    # Act
    browser_tools.goto(page, url)
    assert _wait_first(page, capturer) is True
    payload = capturer.payloads[0]

    # Assert
    assert payload['utm_source'] == 'playwright'
    assert payload['utm_medium'] == 'e2e'
    assert payload['utm_campaign'] == ''
    assert payload['utm_content'] == ''


@pytest.mark.app
def test_tracking_payload_viewport_reflects_window_size(
    browser: Browser,
    subdomain: Callable[[str], str],
) -> None:
    """El viewport del payload refleja el tamano real de la ventana.

    Given un contexto con viewport 1280x800 y `/track` interceptado,
    When se carga `/`,
    Then `viewport_width` es 1280 y `viewport_height` esta en [600, 800].
    """
    # Arrange
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
    )
    page = context.new_page()
    try:
        browser_tools.disable_send_beacon(page)
        capturer = browser_tools.capture_track(page)

        # Act
        browser_tools.goto(page, f'{subdomain("generic")}/')
        assert _wait_first(page, capturer) is True
        payload = capturer.payloads[0]

        # Assert
        assert payload['viewport_width'] == 1280
        assert 600 <= int(payload['viewport_height']) <= 800
    finally:
        page.close()
        context.close()
