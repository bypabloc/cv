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
import pytest
from shared import browser as browser_tools


def _goto_contact_ready(page: Page, origin: str) -> None:
    """Navega a /contact y espera a que el island React HIDRATE.

    El form lo monta un `<astro-island client:load>`. El SSR de Astro pinta el
    markup inmediatamente (form + inputs en el DOM), pero los handlers de React
    (onChange/onBlur/onSubmit) solo existen cuando el island HIDRATA. Esperar
    solo a que el form este en el DOM NO basta: contra dev la hidratacion tarda
    y los tests interactuarian con handlers aun no montados (flaky).

    Astro elimina la propiedad interna del custom element al hidratar; la senal
    fiable y barata es que el `<astro-island>` que envuelve el form ya no este
    marcado como pendiente (`ssr`)/sin hidratar. NO usar `networkidle`: el
    TrackingPixel emite requests continuos y la red nunca queda idle.
    """
    browser_tools.goto(page, f'{origin}/contact')
    browser_tools.wait_selector(page, '[data-testid="contact-form"]')
    browser_tools.wait_selector(page, 'input[name="name"]')
    # El island esta hidratado cuando su <astro-island> contenedor ya no tiene
    # el atributo `ssr` (Astro lo quita al hidratar el componente client:load).
    # Timeout explicito de 60s (no el default de 30s): contra dev el cold-start
    # del Pages project + la descarga del bundle del island puede superar 30s
    # de forma intermitente (flake observado). La espera termina apenas hidrata,
    # asi que NO penaliza el caso warm.
    page.wait_for_function(
        """() => {
            const form = document.querySelector('[data-testid="contact-form"]');
            if (!form) return false;
            const island = form.closest('astro-island');
            // Sin <astro-island> (otro montaje) o ya hidratado (sin attr ssr).
            return !island || !island.hasAttribute('ssr');
        }""",
        timeout=60_000,
    )


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
def test_contact_form_invalid_email_submit_shows_format_error(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Email invalido al enviar muestra error de formato; al corregir desaparece.

    Given el form de contacto,
    When se escribe un email invalido y se envia, y luego se corrige,
    Then primero aparece el error de formato exacto y al corregir desaparece.

    Nota: la validacion on-BLUR (handleBlur) se prueba en el unit test
    `packages/ui/tests/unit/contact-form-schema.test.ts` (hidratacion
    instantanea en jsdom). Aqui se dispara via SUBMIT (click), que espera la
    accionabilidad del boton -> garantiza que el island ya hidrato; el blur es
    un evento efimero que contra dev se pierde si el island aun no monto los
    handlers (flaky). El submit cubre el mismo comportamiento observable de
    forma determinista.
    """
    # Arrange
    _goto_contact_ready(page, subdomain('generic'))
    email_input = page.locator('input[name="email"]')
    error_email = page.locator('[data-testid="error-email"]')

    # Act: email invalido + submit (el click espera hidratacion del island).
    email_input.fill('no-es-email')
    page.locator('[data-testid="contact-submit"]').click()
    error_email.wait_for(state='visible')

    # Assert: error de formato exacto
    assert error_email.inner_text() == 'Email invalido. Revisa el formato.'

    # Act - corregir el email (re-validacion al tipear)
    email_input.fill('pacg1991@gmail.com')

    # Assert: el error de formato desaparece
    error_email.wait_for(state='hidden')
    assert error_email.is_hidden() is True


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
    # Tras el reload el island React re-hidrata para leer localStorage y
    # renderizar la card; contra dev (cold-start) puede tardar mas de 30s.
    browser_tools.wait_selector(
        page,
        '[data-testid="contact-sent-card"]',
        timeout=60_000,
    )

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
    # Re-hidratacion del island tras el reload (cold-start de dev, ver test
    # de persistencia): timeout extendido para evitar flake.
    browser_tools.wait_selector(
        page,
        '[data-testid="contact-sent-card"]',
        timeout=60_000,
    )

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
