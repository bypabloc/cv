/**
 * @feature Embudo de contacto (SPEC-200 AC-4, AC-5)
 * @description Verifica que el formulario de contacto emite los eventos del
 *   embudo PREVIOS al envio via `trackEvent`:
 *   - `contact_view` al cargar /contact [AC-4]
 *   - `contact_form_start` en el primer foco de un campo [AC-5]
 *
 *   Los eventos de ENVIO (`contact_form_submit` + `contact_form_success` /
 *   `contact_form_error`, AC-6/AC-7) NO se prueban desde el browser: el form
 *   exige el widget Turnstile real y ya NO hay bypass desde el frontend. El
 *   embudo de envio se valida server-to-server con el CLI `api_e2e`.
 *
 *   Tracking always-on: los eventos se emiten sin gating de consentimiento.
 *   Los eventos viajan por `navigator.sendBeacon`; el test lo neutraliza con
 *   `addInitScript` para que `trackEvent` caiga al path `fetch`, cuyo
 *   `postData` SI es legible por Playwright.
 */
import { expect, type Page, subdomainUrl, test } from '../fixtures/index.js'

const EVENT_TYPES = {
  CONTACT_VIEW: '019e372b-e0a7-7f8f-b568-3fbdb8a91756',
  CONTACT_FORM_START: '019e372b-e0a7-7467-a074-603b7e294cf8',
} as const

interface TrackPayload {
  session_id: string
  event_id: string
  event_type_id: string
  page_url: string
  event_props?: Record<string, unknown>
  [key: string]: unknown
}

/**
 * Deshabilita `navigator.sendBeacon` para forzar el fallback a `fetch()`
 * (cuyo postData Playwright SI expone de forma fiable).
 */
async function disableSendBeacon(page: Page): Promise<void> {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'sendBeacon', {
      configurable: true,
      value: undefined,
    })
  })
}

/**
 * Intercepta los POST a `/track`, los responde 204 y acumula sus payloads.
 */
async function captureTrackRequests(page: Page): Promise<TrackPayload[]> {
  const captured: TrackPayload[] = []
  await page.route('**/track', async (route) => {
    const request = route.request()
    if (request.method() === 'POST') {
      try {
        captured.push(JSON.parse(request.postData() ?? '{}') as TrackPayload)
      } catch {
        // payload no JSON: lo ignoramos
      }
    }
    await route.fulfill({ status: 204, body: '' })
  })
  return captured
}

/**
 * Devuelve los `event_type_id` capturados, en orden de emision.
 */
function emittedTypes(captured: TrackPayload[]): string[] {
  return captured.map((p) => p.event_type_id)
}

/**
 * Navega a /contact y espera a que el island este interactivo de forma
 * estable. En dev (Vite HMR) la primera carga del island puede disparar una
 * re-optimizacion de dependencias que recarga la pagina; esperar el evento
 * `contact_view` capturado garantiza que el island ya monto definitivamente
 * (su effect de montaje ya corrio) — recien ahi es seguro interactuar.
 */
async function gotoContactFunnel(
  page: Page,
  captured: TrackPayload[],
): Promise<void> {
  await page.goto(`${subdomainUrl()}/contact`, {
    waitUntil: 'domcontentloaded',
  })
  await expect(page.locator('input[name="name"]')).toBeVisible()
  await expect
    .poll(() => emittedTypes(captured).includes(EVENT_TYPES.CONTACT_VIEW), {
      timeout: 15000,
    })
    .toBe(true)
}

test.describe('Feature: embudo de contacto (SPEC-200)', () => {
  test('Given /contact When carga Then emite contact_view [AC-4]', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const captured = await captureTrackRequests(page)

    // Act
    await page.goto(`${subdomainUrl()}/contact`, {
      waitUntil: 'domcontentloaded',
    })
    await expect(page.getByTestId('contact-form')).toBeVisible()
    // 15s de margen: en dev la primera carga del island puede recargar por
    // la re-optimizacion de dependencias de Vite.
    await expect
      .poll(() => emittedTypes(captured).includes(EVENT_TYPES.CONTACT_VIEW), {
        timeout: 15000,
      })
      .toBe(true)

    // Assert
    const viewEvent = captured.find(
      (p) => p.event_type_id === EVENT_TYPES.CONTACT_VIEW,
    )
    expect(viewEvent?.page_url).toContain('/contact')
  })

  test('Given el form When foco el primer campo Then emite contact_form_start una vez [AC-5]', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const captured = await captureTrackRequests(page)
    await gotoContactFunnel(page, captured)

    // Act: focar dos campos distintos -> contact_form_start solo una vez
    await page.locator('input[name="name"]').focus()
    await page.locator('input[name="email"]').focus()
    await expect
      .poll(
        () =>
          emittedTypes(captured).filter(
            (t) => t === EVENT_TYPES.CONTACT_FORM_START,
          ).length,
        { timeout: 10000 },
      )
      .toBe(1)

    // Assert: exactamente un contact_form_start pese a multiples focos
    const starts = emittedTypes(captured).filter(
      (t) => t === EVENT_TYPES.CONTACT_FORM_START,
    )
    expect(starts.length).toBe(1)
  })
})
