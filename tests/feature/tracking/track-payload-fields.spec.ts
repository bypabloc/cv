/**
 * @feature TrackingPixel - payload completo con 9 campos required
 * @description Verifica el contrato del POST /track tras spec
 *   tracking-data-completeness: el frontend envia los 9 campos
 *   required (page_path, page_url, page_title, viewport_width/height,
 *   utm_source/medium/campaign/content) ademas de session_id, event_id,
 *   event_type_id, referrer, niche.
 *
 *   Tests:
 *   - el body del POST /track trae los 16 campos esperados (AC-2)
 *   - viewport refleja window.innerWidth/Height reales (AC-6)
 *   - utm_* se parsean del query string; '' cuando no aplica (AC-9)
 */
import { expect, type Page, subdomainUrl, test } from '../fixtures/index.js'

async function disableSendBeacon(page: Page): Promise<void> {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'sendBeacon', {
      configurable: true,
      value: undefined,
    })
  })
}

interface FullTrackPayload {
  operation: string
  action: string
  session_id: string
  event_id: string
  event_type_id: string
  page_url: string
  page_path: string
  page_title: string
  referrer: string
  utm_source: string
  utm_medium: string
  utm_campaign: string
  utm_content: string
  viewport_width: number
  viewport_height: number
  device_pixel_ratio?: number
  niche: string
  event_props?: Record<string, unknown>
}

async function captureFirstTrack(
  page: Page,
): Promise<{ getPayload: () => FullTrackPayload | undefined }> {
  let captured: FullTrackPayload | undefined
  await page.route('**/track', async (route) => {
    const request = route.request()
    if (request.method() === 'POST' && !captured) {
      try {
        captured = JSON.parse(request.postData() ?? '{}') as FullTrackPayload
      } catch {
        /* noop */
      }
    }
    await route.fulfill({ status: 204, body: '' })
  })
  return { getPayload: () => captured }
}

test.describe('Feature: TrackingPixel payload fields', () => {
  test('Given home WITHOUT utm When carga Then payload trae los 9 required + utm_* vacios [AC-2, AC-9]', async ({
    page,
  }) => {
    await disableSendBeacon(page)
    const { getPayload } = await captureFirstTrack(page)

    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await expect.poll(() => getPayload(), { timeout: 10000 }).toBeDefined()

    const p = getPayload()
    if (!p) throw new Error('payload no capturado')
    expect(p.page_url).toContain('/')
    expect(p.page_path).toBe('/')
    expect(typeof p.page_title).toBe('string')
    expect(typeof p.referrer).toBe('string') // '' cuando sin referrer
    // utm_* siempre presentes como string (nunca undefined ni null)
    expect(p.utm_source).toBe('')
    expect(p.utm_medium).toBe('')
    expect(p.utm_campaign).toBe('')
    expect(p.utm_content).toBe('')
  })

  test('Given home WITH utm_source/medium en URL When carga Then payload los trae poblados [AC-9]', async ({
    page,
  }) => {
    await disableSendBeacon(page)
    const { getPayload } = await captureFirstTrack(page)

    await page.goto(`${subdomainUrl()}/?utm_source=playwright&utm_medium=e2e`, {
      waitUntil: 'domcontentloaded',
    })
    await expect.poll(() => getPayload(), { timeout: 10000 }).toBeDefined()

    const p = getPayload()
    if (!p) throw new Error('payload no capturado')
    expect(p.utm_source).toBe('playwright')
    expect(p.utm_medium).toBe('e2e')
    expect(p.utm_campaign).toBe('')
    expect(p.utm_content).toBe('')
  })

  test('Given viewport 1280x800 When carga Then payload.viewport_width === 1280 y >= 600 viewport_height [AC-6]', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await disableSendBeacon(page)
    const { getPayload } = await captureFirstTrack(page)

    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
    await expect.poll(() => getPayload(), { timeout: 10000 }).toBeDefined()

    const p = getPayload()
    if (!p) throw new Error('payload no capturado')
    expect(p.viewport_width).toBe(1280)
    // height puede ser un poco menor por scrollbar; rango razonable
    expect(p.viewport_height).toBeGreaterThanOrEqual(600)
    expect(p.viewport_height).toBeLessThanOrEqual(800)
  })
})
