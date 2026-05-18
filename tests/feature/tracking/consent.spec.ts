/**
 * @feature CookieBanner - consentimiento GDPR (SPEC-201)
 * @description Verifica el flujo de consentimiento end-to-end:
 *   - primera visita muestra el banner [AC-1]
 *   - Rechazar persiste 'rejected' y NO emite POST /track [AC-2]
 *   - Aceptar persiste 'accepted' y emite page_load [AC-3]
 *   - segunda visita tras responder NO muestra el banner [AC-4]
 *   - el enlace del Footer reabre el banner [AC-5]
 *   - reabrir y rechazar tras aceptar cesa el tracking [AC-6]
 *   - el banner es navegable con teclado (Tab alcanza ambos botones) [AC-7]
 *
 *   El pixel envia por navigator.sendBeacon; Playwright no expone su
 *   postData de forma fiable, asi que se neutraliza sendBeacon con
 *   addInitScript para que el pixel caiga al path fetch (interceptable).
 */
import { expect, type Page, subdomainUrl, test } from '../fixtures/index.js'

/**
 * Deshabilita navigator.sendBeacon para forzar el fallback a fetch() del
 * pixel. fetch expone postData de forma fiable; sendBeacon (Blob) no.
 */
async function disableSendBeacon(page: Page): Promise<void> {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'sendBeacon', {
      configurable: true,
      value: undefined,
    })
  })
}

interface TrackPayload {
  event_type_id: string
  [key: string]: unknown
}

/**
 * Intercepta los POST a /track, los responde 204 (sin depender del backend
 * AWS) y acumula los payloads en el array devuelto.
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

const PAGE_LOAD_TYPE = '019e372b-e0a7-7154-8279-8829bcf6a08c'

test.describe('Feature: CookieBanner consentimiento GDPR (SPEC-201)', () => {
  test('Given primera visita When carga Then el banner es visible con dos botones [AC-1]', async ({
    page,
  }) => {
    // Act
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    // Assert
    const banner = page.getByRole('dialog', {
      name: 'Consentimiento de analytics',
    })
    await expect(banner).toBeVisible()
    await expect(page.getByTestId('cookie-accept')).toBeVisible()
    await expect(page.getByTestId('cookie-reject')).toBeVisible()
  })

  test('Given el banner visible When click Rechazar Then cf_consent=rejected, banner oculto y sin POST /track [AC-2]', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const captured = await captureTrackRequests(page)

    // Act
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('cookie-reject').click()
    await page.waitForTimeout(4000)

    // Assert
    const consent = await page.evaluate(() =>
      localStorage.getItem('cf_consent'),
    )
    expect(consent).toBe('rejected')
    await expect(page.getByRole('dialog')).toBeHidden()
    expect(captured.length).toBe(0)
  })

  test('Given el banner visible When click Aceptar Then cf_consent=accepted, banner oculto y emite page_load [AC-3]', async ({
    page,
  }) => {
    // Arrange
    await disableSendBeacon(page)
    const captured = await captureTrackRequests(page)

    // Act
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('cookie-accept').click()
    await expect.poll(() => captured.length, { timeout: 5000 }).toBe(1)

    // Assert
    const consent = await page.evaluate(() =>
      localStorage.getItem('cf_consent'),
    )
    expect(consent).toBe('accepted')
    await expect(page.getByRole('dialog')).toBeHidden()
    expect(captured[0].event_type_id).toBe(PAGE_LOAD_TYPE)
  })

  test('Given un usuario que ya respondio When vuelve a abrir Then el banner NO se muestra [AC-4]', async ({
    page,
  }) => {
    // Arrange: primera visita + rechazar
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('cookie-reject').click()
    await expect(page.getByRole('dialog')).toBeHidden()

    // Act: segunda visita en la misma sesion del browser
    await page.goto(`${subdomainUrl()}/about`, {
      waitUntil: 'domcontentloaded',
    })
    await page.waitForTimeout(1000)

    // Assert
    await expect(page.getByRole('dialog')).toBeHidden()
  })

  test('Given el enlace del Footer When lo activo Then el banner se reabre [AC-5]', async ({
    page,
  }) => {
    // Arrange: aceptar para que el banner quede cerrado
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('cookie-accept').click()
    await expect(page.getByRole('dialog')).toBeHidden()

    // Act: activar "Gestionar consentimiento" en el Footer
    await page.getByTestId('manage-consent').click()

    // Assert: el banner reaparece
    await expect(page.getByRole('dialog')).toBeVisible()
  })

  test('Given cf_consent=accepted When reabro y rechazo Then cf_consent=rejected y cesa el tracking [AC-6]', async ({
    page,
  }) => {
    // Arrange: aceptar primero
    await disableSendBeacon(page)
    const captured = await captureTrackRequests(page)
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('cookie-accept').click()
    await expect.poll(() => captured.length, { timeout: 5000 }).toBe(1)

    // Act: reabrir desde el Footer y rechazar
    await page.getByTestId('manage-consent').click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await page.getByTestId('cookie-reject').click()

    // Assert: el consentimiento quedo revocado y un reload no emite mas
    const consent = await page.evaluate(() =>
      localStorage.getItem('cf_consent'),
    )
    expect(consent).toBe('rejected')
    const before = captured.length
    await page.goto(`${subdomainUrl()}/about`, {
      waitUntil: 'domcontentloaded',
    })
    await page.waitForTimeout(4000)
    expect(captured.length).toBe(before)
  })

  test('Given el banner When navego con teclado Then Tab alcanza ambos botones con foco visible [AC-7]', async ({
    page,
  }) => {
    // Act
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('dialog')).toBeVisible()

    // Assert: al abrir el foco entra al boton Aceptar
    const accept = page.getByTestId('cookie-accept')
    const reject = page.getByTestId('cookie-reject')
    await expect(accept).toBeFocused()

    // Tab mueve el foco al boton Rechazar
    await page.keyboard.press('Tab')
    await expect(reject).toBeFocused()

    // Enter sobre el boton enfocado activa el rechazo
    await page.keyboard.press('Enter')
    await expect(page.getByRole('dialog')).toBeHidden()
    const consent = await page.evaluate(() =>
      localStorage.getItem('cf_consent'),
    )
    expect(consent).toBe('rejected')
  })

  test('Given el layout en ingles When carga /en/ Then el banner muestra textos en ingles [AC-8]', async ({
    page,
  }) => {
    // Act
    await page.goto(`${subdomainUrl()}/en/`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    await expect(page.getByTestId('cookie-accept')).toHaveText('Accept')
    await expect(page.getByTestId('cookie-reject')).toHaveText('Reject')
  })
})
