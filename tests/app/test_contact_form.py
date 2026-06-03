"""Contact form (React + Zod): validacion client-side + persistencia (AC-3).

Porta `tests/feature/contact/contact-form.spec.ts`: lo que el browser puede
verificar SIN enviar el form (el envio real exige Turnstile y se cubre
server-to-server en el modulo `api`):
  1. Validacion Zod en cliente (errores por campo en submit vacio + formato
     de email en blur).
  2. Persistencia: con un record en `localStorage`, recargar muestra la card
     de "enviado" en vez del form.
  3. "Enviar otro mensaje" limpia el storage y re-muestra el form.

NINGUN test envia el form ni muta el backend desplegado: el envio se simula
seteando `localStorage` directo.
"""

from __future__ import annotations

from collections.abc import Callable

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import pytest
from shared import browser as browser_tools


def _goto_contact_ready(page: Page, origin: str) -> None:
    """Navega a /contact y espera a que el island React hidrate.

    NO usar `wait_for_load_state('networkidle')`: el TrackingPixel del sitio
    emite requests de forma continua, asi que la red NUNCA queda idle contra
    dev y el wait agota el timeout. Esperar el form + el input rendereados por
    el SSR de Astro alcanza para los flujos de submit/reload; el flujo on-blur
    (evento unico que se puede perder si el handler aun no monto) reintenta el
    blur en su propio test.
    """
    browser_tools.goto(page, f'{origin}/contact')
    browser_tools.wait_selector(page, '[data-testid="contact-form"]')
    browser_tools.wait_selector(page, 'input[name="name"]')


def _seed_contact_sent(page: Page, contact_id: str) -> None:
    """Setea un record de contacto enviado (no expirado) en localStorage."""
    page.evaluate(
        '(contactId) => {'
        '  const future = Date.now() + 7 * 24 * 60 * 60 * 1000;'
        "  window.localStorage.setItem('contact_sent', JSON.stringify({"
        '    contactId, sentAt: Date.now(), expiresAt: future }));'
        '}',
        contact_id,
    )


@pytest.mark.app
def test_contact_form_empty_submit_shows_zod_errors(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Submit con el form vacio muestra los 3 errores Zod por campo.

    Given el form de contacto hidratado en el apex,
    When se hace submit sin llenar nada,
    Then aparecen los errores exactos de name, email y message.
    """
    # Arrange
    _goto_contact_ready(page, subdomain('generic'))

    # Act
    page.locator('[data-testid="contact-submit"]').click()
    browser_tools.wait_selector(page, '[data-testid="error-name"]')

    # Assert
    assert (
        page.locator('[data-testid="error-name"]').inner_text()
        == 'Minimo 2 caracteres.'
    )
    assert (
        page.locator('[data-testid="error-email"]').inner_text()
        == 'El email es obligatorio.'
    )
    assert (
        page.locator('[data-testid="error-message"]').inner_text()
        == 'Minimo 10 caracteres.'
    )


@pytest.mark.app
def test_contact_form_invalid_email_blur_shows_format_error(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Email invalido en blur muestra error de formato; al corregir desaparece.

    Given el form de contacto hidratado,
    When se escribe un email invalido y se hace blur, y luego se corrige,
    Then primero aparece el error de formato exacto y al corregir el error se
    oculta.
    """
    # Arrange
    _goto_contact_ready(page, subdomain('generic'))
    email_input = page.locator('input[name="email"]')
    error_email = page.locator('[data-testid="error-email"]')

    # Act: llenar un email invalido y disparar blur (valida on-blur). Contra
    # dev el handleBlur de React puede no estar montado en el primer blur si
    # la hidratacion del island aun no concluyo; reintentar el blur hasta que
    # el error aparezca (o agotar) tolera esa ventana sin sleeps fijos.
    email_input.fill('no-es-email')
    for _ in range(10):
        email_input.blur()
        try:
            error_email.wait_for(state='visible', timeout=3000)
            break
        except PlaywrightTimeoutError:
            email_input.focus()  # re-tocar el campo y reintentar el blur

    # Assert: error de formato exacto
    assert error_email.inner_text() == 'Email invalido. Revisa el formato.'

    # Act - corregir el email
    email_input.fill('pacg1991@gmail.com')

    # Assert: el error desaparece (re-validacion al tipear)
    page.locator('[data-testid="error-email"]').wait_for(state='hidden')
    assert page.locator('[data-testid="error-email"]').is_hidden() is True


@pytest.mark.app
def test_contact_form_persisted_record_shows_sent_card_on_reload(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Con un record en localStorage, recargar muestra la card de enviado.

    Given el form de contacto y un record `contact_sent` valido seteado en
    localStorage,
    When se recarga la pagina,
    Then se muestra la card de enviado con el id exacto y el form queda
    oculto.
    """
    # Arrange
    contact_id = '019e28fc-b97d-7d79-91a5-44c9b19465b4'
    _goto_contact_ready(page, subdomain('generic'))
    _seed_contact_sent(page, contact_id)

    # Act
    page.reload(wait_until='domcontentloaded')
    browser_tools.wait_selector(page, '[data-testid="contact-sent-card"]')

    # Assert
    assert (
        page.locator('[data-testid="contact-sent-card"]').is_visible() is True
    )
    assert (
        page.locator('[data-testid="contact-sent-id"]').inner_text()
        == contact_id
    )
    assert page.locator('[data-testid="contact-form"]').is_hidden() is True


@pytest.mark.app
def test_contact_form_resend_button_clears_storage_and_shows_form(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """ "Enviar otro mensaje" limpia localStorage y vuelve a mostrar el form.

    Given la card de enviado visible (record en localStorage),
    When se hace click en "Enviar otro mensaje",
    Then el form vuelve a aparecer, la card se oculta y `contact_sent` queda
    borrado de localStorage.
    """
    # Arrange
    _goto_contact_ready(page, subdomain('generic'))
    _seed_contact_sent(page, 'test-resend-id')
    page.reload(wait_until='domcontentloaded')
    browser_tools.wait_selector(page, '[data-testid="contact-sent-card"]')

    # Act
    page.locator('[data-testid="contact-resend-btn"]').click()
    browser_tools.wait_selector(page, '[data-testid="contact-form"]')

    # Assert
    assert page.locator('[data-testid="contact-form"]').is_visible() is True
    assert page.locator('[data-testid="contact-sent-card"]').is_hidden() is True
    stored = page.evaluate(
        "() => window.localStorage.getItem('contact_sent')",
    )
    assert stored is None
