/**
 * @feature Enlace contacto <-> tracking via session_id (SPEC-202 AC-1/AC-2)
 * @description Verifica que el formulario de contacto envia el `session_id`
 *   de tracking en el body del `POST /contact`:
 *   - Con tracking aceptado: el `session_id` del `POST /contact` es el MISMO
 *     que el de los eventos de `/track` (misma `localStorage.cf_session`)
 *     [AC-1].
 *   - Con tracking rechazado (sin `cf_session`): el contacto se envia SIN la
 *     clave `session_id` y el form igual funciona [AC-2].
 *
 *   El `POST /contact` se intercepta con `page.route` para inspeccionar el
 *   body sin depender del backend AWS. El bypass de Turnstile se inyecta solo
 *   si `TURNSTILE_BYPASS_SECRET` esta seteada; sin el, el preflight del form
 *   exige captcha y no llega a hacer el POST, asi que esos tests se skipean.
 */
import { expect, type Page, subdomainUrl, test } from '../fixtures/index.js'

const BYPASS_SECRET = process.env.TURNSTILE_BYPASS_SECRET ?? ''

const CONTACT_ROUTE =
  /https:\/\/[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com\/[a-z]+\/contact$/

interface ContactPayload {
  name?: string
  email?: string
  message?: string
  session_id?: string
  [key: string]: unknown
}

interface TrackPayload {
  session_id: string
  event_type_id: string
  [key: string]: unknown
}

/**
 * Deshabilita `navigator.sendBeacon` para que los eventos de `/track`
 * caigan al path `fetch` (postData legible).
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
 * Intercepta el `POST /contact` (al API Gateway), responde 201 y captura el
 * body en el array devuelto.
 */
async function captureContactPosts(page: Page): Promise<ContactPayload[]> {
  const captured: ContactPayload[] = []
  await page.route(CONTACT_ROUTE, async (route) => {
    if (route.request().method() === 'POST') {
      try {
        captured.push(
          JSON.parse(route.request().postData() ?? '{}') as ContactPayload,
        )
      } catch {
        // payload no JSON: lo ignoramos
      }
    }
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        contact_id: '019e28fc-b97d-7d79-91a5-44c9b19465b4',
        created_at: new Date().toISOString(),
      }),
    })
  })
  return captured
}

/**
 * Intercepta los POST a `/track` y captura sus payloads.
 */
async function captureTrackRequests(page: Page): Promise<TrackPayload[]> {
  const captured: TrackPayload[] = []
  await page.route('**/track', async (route) => {
    if (route.request().method() === 'POST') {
      try {
        captured.push(
          JSON.parse(route.request().postData() ?? '{}') as TrackPayload,
        )
      } catch {
        // payload no JSON: lo ignoramos
      }
    }
    await route.fulfill({ status: 204, body: '' })
  })
  return captured
}

const MESSAGE = 'Mensaje suficientemente largo para pasar Zod cliente.'

/**
 * Rellena los campos obligatorios del form con datos validos y verifica que
 * los valores se mantienen. En dev (Vite HMR) la primera carga del island
 * puede recargar la pagina por la re-optimizacion de dependencias, lo que
 * borraria los valores controlados por React; el poll re-rellena hasta que
 * el form queda estable.
 */
async function fillContactForm(page: Page): Promise<void> {
  await expect
    .poll(
      async () => {
        await page.locator('input[name="name"]').fill('Pablo Session')
        await page.locator('input[name="email"]').fill('pacg1991@gmail.com')
        await page.locator('textarea[name="message"]').fill(MESSAGE)
        return page.locator('input[name="name"]').inputValue()
      },
      { timeout: 15000 },
    )
    .toBe('Pablo Session')
}

/**
 * Espera a que el island este interactivo de forma estable. Sin
 * consentimiento el island no emite `/track`: la estabilidad se verifica con
 * `fillContactForm`, que re-rellena hasta que los valores se mantienen.
 */
async function waitIslandReady(page: Page): Promise<void> {
  await expect(page.locator('input[name="name"]')).toBeVisible()
}

test.describe('Feature: enlace contacto <-> tracking por session_id (SPEC-202)', () => {
  test.skip(
    !BYPASS_SECRET,
    'TURNSTILE_BYPASS_SECRET no esta seteada: el form exige captcha',
  )

  test.beforeEach(async ({ page }) => {
    await page.addInitScript((secret: string) => {
      ;(
        window as Window & { __playwrightTurnstileBypass?: string }
      ).__playwrightTurnstileBypass = secret
    }, BYPASS_SECRET)
  })

  test('Given tracking aceptado When envio el form Then el POST /contact lleva el mismo session_id que /track [AC-1]', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const contactPosts = await captureContactPosts(page)
    const trackPosts = await captureTrackRequests(page)

    // Act: con ?cf_track=force el tracking emite eventos -> hay cf_session
    await page.goto(`${subdomainUrl()}/contact?cf_track=force`, {
      waitUntil: 'domcontentloaded',
    })
    await waitIslandReady(page)
    // fillContactForm re-rellena si Vite recarga el island; tras completarse,
    // el form esta estable y el embudo ya emitio al menos un /track.
    await fillContactForm(page)
    await expect
      .poll(() => trackPosts.length, { timeout: 15000 })
      .toBeGreaterThanOrEqual(1)
    await page.getByTestId('contact-submit').click()
    await expect.poll(() => contactPosts.length, { timeout: 10000 }).toBe(1)

    // Assert: el session_id del contacto coincide con el de los eventos
    const trackingSessionId = trackPosts[0].session_id
    expect(trackingSessionId.length).toBeGreaterThanOrEqual(20)
    expect(contactPosts[0].session_id).toBe(trackingSessionId)
  })

  test('Given tracking rechazado When envio el form Then el POST /contact NO lleva session_id [AC-2]', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const contactPosts = await captureContactPosts(page)

    // Act: SIN ?cf_track=force y sin cf_consent -> no hay cf_session
    await page.goto(`${subdomainUrl()}/contact`, {
      waitUntil: 'domcontentloaded',
    })
    await waitIslandReady(page)
    // fillContactForm re-rellena si Vite recarga el island; al terminar el
    // form esta estable. Recien entonces se limpia el storage de tracking.
    await fillContactForm(page)
    await page.evaluate(() => {
      window.localStorage.removeItem('cf_session')
      window.localStorage.removeItem('cf_consent')
    })
    await page.getByTestId('contact-submit').click()
    await expect.poll(() => contactPosts.length, { timeout: 10000 }).toBe(1)

    // Assert: el contacto se envia y NO incluye la clave session_id
    expect('session_id' in contactPosts[0]).toBe(false)
    expect(contactPosts[0].name).toBe('Pablo Session')
  })
})
