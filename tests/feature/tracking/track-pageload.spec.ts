/**
 * @feature TrackingPixel - tracking always-on en las 6 apps
 * @description Verifica el cableado end-to-end del TrackingPixel:
 *   - cada subdominio emite POST /track con event_id + event_type_id al cargar
 *     SIN requerir opt-in previo (tracking always-on, sin gating)
 *   - la navegacion SPA (View Transitions) re-dispara un page_load nuevo
 *   - NO existe banner de consentimiento ni boton "Gestionar consentimiento"
 *     en el DOM [AC-1, AC-4]
 *
 *   El pixel envia el evento por navigator.sendBeacon (con fallback a fetch).
 *   El body de sendBeacon viaja como Blob y Playwright no expone su postData
 *   de forma fiable, asi que el test neutraliza sendBeacon con addInitScript:
 *   el pixel cae al path `fetch`, cuyo postData SI es legible.
 */
import { expect, type Page, subdomainUrl, test } from '../fixtures/index.js'

/**
 * Deshabilita navigator.sendBeacon para forzar el fallback a fetch() del
 * pixel. fetch expone el postData de forma fiable en Playwright; sendBeacon
 * (que envia un Blob) no.
 */
async function disableSendBeacon(page: Page): Promise<void> {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'sendBeacon', {
      configurable: true,
      value: undefined,
    })
  })
}

const UUID_RE =
  /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i
const PAGE_LOAD_TYPE = '019e372b-e0a7-7154-8279-8829bcf6a08c'

const SUBDOMAINS = [
  { name: 'generic (apex)', host: undefined },
  { name: 'hub', host: 'hub' },
  { name: 'fintech', host: 'fintech' },
  { name: 'architect', host: 'architect' },
  { name: 'leader', host: 'leader' },
  { name: 'vibe', host: 'vibe' },
] as const

interface TrackPayload {
  session_id: string
  event_id: string
  event_type_id: string
  page_url: string
  [key: string]: unknown
}

/**
 * Intercepta los POST a `/track` con page.route, los responde 204 (sin
 * depender del backend AWS) y acumula los payloads en el array devuelto.
 *
 * Requiere disableSendBeacon: con sendBeacon deshabilitado el pixel usa
 * fetch(), que page.route SI intercepta.
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
 * Espera (poll) hasta que `captured` tenga al menos `min` elementos.
 */
async function waitForCount(
  captured: TrackPayload[],
  min: number,
): Promise<void> {
  await expect
    .poll(() => captured.length, { timeout: 10000 })
    .toBeGreaterThanOrEqual(min)
}

test.describe('Feature: TrackingPixel always-on', () => {
  for (const { name, host } of SUBDOMAINS) {
    test(`Given ${name} When carga Then emite POST /track con event_type_id (sin opt-in) [AC-2]`, async ({
      page,
    }) => {
      // Arrange
      await disableSendBeacon(page)
      const captured = await captureTrackRequests(page)

      // Act
      await page.goto(`${subdomainUrl(host)}/`, {
        waitUntil: 'domcontentloaded',
      })
      await waitForCount(captured, 1)

      // Assert
      const payload = captured[0]
      expect(payload.event_type_id).toBe(PAGE_LOAD_TYPE)
      expect(payload.event_id).toMatch(UUID_RE)
      expect(payload.session_id.length).toBeGreaterThanOrEqual(20)
      expect(payload.page_url).toContain(host ?? 'localhost')
    })
  }

  test('Given carga inicial When inspecciono Then NO existe banner ni boton Gestionar consentimiento [AC-1, AC-4]', async ({
    page,
  }) => {
    // Act
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    // Assert: ningun dialogo con label de consent en ES ni en EN
    await expect(
      page.getByRole('dialog', {
        name: /Consentimiento de analytics|Analytics consent/i,
      }),
    ).toHaveCount(0)
    // El boton del Footer ya no existe
    await expect(page.locator('[data-testid="manage-consent"]')).toHaveCount(0)
    // El elemento del banner tampoco
    await expect(page.locator('#cookie-banner')).toHaveCount(0)
  })

  test('Given dos cargas en la misma sesion When inspecciono Then mismo session_id y event_id distinto', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const captured = await captureTrackRequests(page)
    const base = subdomainUrl()

    // Act: dos cargas completas (full reload) en la misma sesion del browser
    await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' })
    await waitForCount(captured, 1)
    await page.goto(`${base}/about`, { waitUntil: 'domcontentloaded' })
    await waitForCount(captured, 2)

    // Assert
    expect(captured[0].session_id).toBe(captured[1].session_id)
    expect(captured[0].event_id).not.toBe(captured[1].event_id)
  })

  test('Given navegacion SPA de / a /about When after-swap Then segundo /track con page_url nueva [AC-3]', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const captured = await captureTrackRequests(page)

    // Act: cargar el home y navegar via View Transition
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await waitForCount(captured, 1)

    await page.evaluate(() => {
      const nav = (window as unknown as { navigate?: (href: string) => void })
        .navigate
      // Astro expone navigate() con ClientRouter activo; fallback a location.
      if (nav) {
        nav('/about')
      } else {
        window.location.href = '/about'
      }
    })

    // Esperar el evento de /about. Segun el browser, entre el page_load del
    // home y el evento de /about puede colarse un spa_navigation intermedio
    // (ClientRouter dispara astro:after-swap antes de que location refleje la
    // ruta nueva en WebKit). Por eso se poll-ea por el evento cuya page_url ya
    // apunta a /about en vez de asumir un orden/conteo fijo.
    await expect
      .poll(() => captured.some((p) => p.page_url.includes('/about')), {
        timeout: 10000,
      })
      .toBe(true)

    // Assert: existe un evento de /about con event_id propio
    const aboutEvent = captured.find((p) => p.page_url.includes('/about'))
    expect(aboutEvent?.page_url).toContain('/about')
    expect(aboutEvent?.event_id).not.toBe(captured[0].event_id)
  })
})
