"""Embudo de contacto: contact_view + contact_form_start (AC-3).

Porta `tests/feature/contact/contact-funnel.spec.ts`: el form emite los
eventos del embudo PREVIOS al envio via `trackEvent`:
  - `contact_view` al cargar /contact.
  - `contact_form_start` una sola vez en el primer foco de un campo.

Tracking always-on (sin gating de consentimiento). Los eventos viajan por
`navigator.sendBeacon`; el test lo neutraliza (`disable_send_beacon`) para
que `trackEvent` caiga al `fetch`, cuyo body SI es legible. SIEMPRE
intercepta `POST /track` con `capture_track` (responde 204 local): NUNCA
deja pasar el request real -> no muta el backend desplegado.
"""

from __future__ import annotations

from collections.abc import Callable

from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools
from shared.browser import TrackCapturer


# event_type_id del catalogo taxonomy (deben coincidir con el frontend).
_CONTACT_VIEW = '019e372b-e0a7-7f8f-b568-3fbdb8a91756'
_CONTACT_FORM_START = '019e372b-e0a7-7467-a074-603b7e294cf8'

# 20s en steps de 200ms: cubre el cold start del primer load de la sesion.
_POLL_STEPS = 100
_POLL_INTERVAL_MS = 200


def _emitted_types(capturer: TrackCapturer) -> list[str]:
    """event_type_id capturados, en orden de emision."""
    return [str(p.get('event_type_id', '')) for p in capturer.payloads]


def _count_type(capturer: TrackCapturer, event_type_id: str) -> int:
    """Cuantas veces se capturo un event_type_id dado."""
    return _emitted_types(capturer).count(event_type_id)


def _poll_until(page: Page, predicate: Callable[[], bool]) -> bool:
    """Poll de `predicate` hasta True o hasta agotar los pasos.

    Usa `page.wait_for_timeout` (NO `time.sleep`): solo `wait_for_timeout`
    bombea el event loop sync de Playwright, dejando que el handler de
    `page.route('**/track')` corra y agregue el payload al capturer. Un
    `time.sleep` puro bloquea sin procesar la request interceptada.
    """
    for _ in range(_POLL_STEPS):
        if predicate():
            return True
        page.wait_for_timeout(_POLL_INTERVAL_MS)
    return predicate()


@pytest.mark.app
def test_contact_funnel_emits_contact_view_on_load(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Cargar /contact emite `contact_view` con la page_url de /contact.

    Given el form de contacto con `/track` interceptado y sendBeacon
    deshabilitado,
    When se carga /contact,
    Then se captura un `contact_view` cuya `page_url` contiene `/contact`.
    """
    # Arrange
    browser_tools.disable_send_beacon(page)
    capturer = browser_tools.capture_track(page)

    # Act
    browser_tools.goto(page, f'{subdomain("generic")}/contact')
    browser_tools.wait_selector(page, '[data-testid="contact-form"]')
    seen = _poll_until(
        page,
        lambda: _CONTACT_VIEW in _emitted_types(capturer),
    )

    # Assert
    assert seen is True
    view_event = next(
        p for p in capturer.payloads if p.get('event_type_id') == _CONTACT_VIEW
    )
    assert '/contact' in str(view_event.get('page_url', ''))


@pytest.mark.app
def test_contact_funnel_emits_form_start_once_on_first_focus(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Focar campos emite `contact_form_start` exactamente una vez.

    Given /contact cargado y el `contact_view` ya emitido,
    When se focan dos campos distintos del form,
    Then `contact_form_start` se captura exactamente una vez (no por cada
    foco).
    """
    # Arrange
    browser_tools.disable_send_beacon(page)
    capturer = browser_tools.capture_track(page)
    browser_tools.goto(page, f'{subdomain("generic")}/contact')
    browser_tools.wait_selector(page, 'input[name="name"]')
    _poll_until(
        page,
        lambda: _CONTACT_VIEW in _emitted_types(capturer),
    )

    # Act
    page.locator('input[name="name"]').focus()
    page.locator('input[name="email"]').focus()
    _poll_until(
        page,
        lambda: _count_type(capturer, _CONTACT_FORM_START) == 1,
    )

    # Assert
    assert _count_type(capturer, _CONTACT_FORM_START) == 1
