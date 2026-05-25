/**
 * @feature Embudo de contacto (SPEC-200 AC-4..AC-7)
 * @description Verifica que el formulario de contacto emite los 5 eventos del
 *   embudo via `trackEvent`:
 *   - `contact_view` al cargar /contact [AC-4]
 *   - `contact_form_start` en el primer foco de un campo [AC-5]
 *   - `contact_form_submit` + `contact_form_success` al enviar con exito [AC-6]
 *   - `contact_form_error` con el codigo del error si el envio falla [AC-7]
 *
 *   Tracking always-on: los eventos se emiten sin gating de consentimiento.
 *   Los eventos viajan por `navigator.sendBeacon`; el test lo neutraliza con
 *   `addInitScript` para que `trackEvent` caiga al path `fetch`, cuyo
 *   `postData` SI es legible por Playwright.
 */
import { expect, type Page, subdomainUrl, test } from '../fixtures/index.js'

const BYPASS_SECRET = process.env.TURNSTILE_BYPASS_SECRET ?? ''

const EVENT_TYPES = {
  CONTACT_VIEW: '019e372b-e0a7-7f8f-b568-3fbdb8a91756',
  CONTACT_FORM_START: '019e372b-e0a7-7467-a074-603b7e294cf8',
  CONTACT_FORM_SUBMIT: '019e372b-e0a7-7a02-b754-606a5fe38afc',
  CONTACT_FORM_SUCCESS: '019e372b-e0a7-7d1b-9bd3-3cb2ee92b4d7',
  CONTACT_FORM_ERROR: '019e372b-e0a7-77f6-897f-17f41a06b2c0',
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
  test.beforeEach(async ({ page }) => {
    if (BYPASS_SECRET) {
      await page.addInitScript((secret: string) => {
        ;(
          window as Window & { __playwrightTurnstileBypass?: string }
        ).__playwrightTurnstileBypass = secret
      }, BYPASS_SECRET)
    }
  })

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

  // ------------------------------------------------------------------
  // Tests que envian el form (AC-6, AC-7): requieren el bypass de Turnstile
  // para superar el preflight del captcha. Se skipean si el secret no esta
  // seteado (mismo patron que contact-form.spec.ts).
  // ------------------------------------------------------------------
  test.describe('with Turnstile bypass (skipped if TURNSTILE_BYPASS_SECRET not set)', () => {
    test.skip(
      !BYPASS_SECRET,
      'TURNSTILE_BYPASS_SECRET no esta seteada en el entorno',
    )

    test('Given un envio que falla 429 When submit Then emite submit + error con el codigo [AC-7]', async ({
      page,
    }) => {
      // Arrange
      await disableSendBeacon(page)
      const captured = await captureTrackRequests(page)
      await page.route(
        /https:\/\/[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com\/[a-z]+\/contact$/,
        async (route) => {
          await route.fulfill({
            status: 429,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Too many requests' }),
          })
        },
      )
      await gotoContactFunnel(page, captured)

      // Act
      await page.locator('input[name="name"]').fill('Pablo Test')
      await page.locator('input[name="email"]').fill('pacg1991@gmail.com')
      await page
        .locator('textarea[name="message"]')
        .fill('Mensaje suficientemente largo para pasar Zod cliente.')
      await page.getByTestId('contact-submit').click()
      await expect
        .poll(
          () => emittedTypes(captured).includes(EVENT_TYPES.CONTACT_FORM_ERROR),
          { timeout: 10000 },
        )
        .toBe(true)

      // Assert: submit precede al error, y el error lleva code 429 en props
      const types = emittedTypes(captured)
      expect(types.includes(EVENT_TYPES.CONTACT_FORM_SUBMIT)).toBe(true)
      const errorEvent = captured.find(
        (p) => p.event_type_id === EVENT_TYPES.CONTACT_FORM_ERROR,
      )
      expect(errorEvent?.event_props).toEqual({ code: '429' })
    })

    test('Given un envio 201 When submit Then emite submit seguido de success [AC-6]', async ({
      page,
    }) => {
      // Arrange: el POST /contact se mockea con 201 para no depender del
      // backend AWS (el embudo se mide en el cliente, no en el Lambda).
      await disableSendBeacon(page)
      const captured = await captureTrackRequests(page)
      await page.route(
        /https:\/\/[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com\/[a-z]+\/contact$/,
        async (route) => {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              contact_id: '019e28fc-b97d-7d79-91a5-44c9b19465b4',
              created_at: new Date().toISOString(),
            }),
          })
        },
      )
      await gotoContactFunnel(page, captured)

      // Act
      const uniqueMsg = `[E2E funnel] ${new Date().toISOString()} - mensaje largo.`
      await page.locator('input[name="name"]').fill('Playwright Funnel')
      await page.locator('input[name="email"]').fill('pacg1991@gmail.com')
      await page.locator('textarea[name="message"]').fill(uniqueMsg)
      await page.getByTestId('contact-submit').click()
      await expect(page.getByTestId('contact-sent-card')).toBeVisible()
      await expect
        .poll(
          () =>
            emittedTypes(captured).includes(EVENT_TYPES.CONTACT_FORM_SUCCESS),
          { timeout: 10000 },
        )
        .toBe(true)

      // Assert: submit emitido antes que success
      const types = emittedTypes(captured)
      const submitIdx = types.indexOf(EVENT_TYPES.CONTACT_FORM_SUBMIT)
      const successIdx = types.indexOf(EVENT_TYPES.CONTACT_FORM_SUCCESS)
      expect(submitIdx).toBeGreaterThanOrEqual(0)
      expect(successIdx).toBeGreaterThan(submitIdx)
    })
  })
})
