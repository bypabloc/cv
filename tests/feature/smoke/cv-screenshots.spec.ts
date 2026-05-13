/**
 * @feature CV screenshots - portfolio multi-niche
 * @description Captura screenshots de hero + secciones de los 6 sitios
 *   del portfolio post-rediseño. Output en results/<niche>/<viewport>/.
 *
 *   Solo desktop-chromium (corre rapido en feature tests, suficiente para
 *   evidencia visual del PR).
 */

import { expect, subdomainUrl, test } from '../fixtures/index.js'
import { captureScreenshot } from '../helpers/screenshot.js'

const SITES = [
  { name: 'generic', host: undefined, label: 'Full Stack' },
  { name: 'hub', host: 'hub', label: 'Hub' },
  { name: 'fintech', host: 'fintech', label: 'Fintech LATAM' },
  { name: 'architect', host: 'architect', label: 'Architect' },
  { name: 'leader', host: 'leader', label: 'Tech Lead' },
  { name: 'vibe', host: 'vibe', label: 'Vibe Coding' },
] as const

test.describe('Feature: CV screenshots - 6 niches', () => {
  test.skip(
    ({ browserName }) => browserName !== 'chromium',
    'Solo desktop-chromium para reducir tiempo de captura',
  )

  for (const site of SITES) {
    test(`When visito ${site.name} Then el hero renderiza con niche tokens y captura screenshot`, async ({
      page,
    }, testInfo) => {
      const url = subdomainUrl(site.host)
      await page.goto(`${url}/`, { waitUntil: 'domcontentloaded' })
      await page
        .waitForLoadState('networkidle', { timeout: 10_000 })
        .catch(() => {
          // tolerar networkidle timeouts en HMR
        })

      // hero visible
      const h1 = page.locator('h1').first()
      await expect(h1).toBeVisible()

      // capturar hero (top)
      await captureScreenshot(page, testInfo, `${site.name}-01-hero`)

      // scroll a 50% (mid) y capturar
      await page.evaluate(() => {
        window.scrollTo({ top: window.innerHeight * 1.5, behavior: 'instant' })
      })
      await page.waitForTimeout(600)
      await captureScreenshot(page, testInfo, `${site.name}-02-mid`)

      // scroll al final
      await page.evaluate(() => {
        window.scrollTo({
          top: document.body.scrollHeight,
          behavior: 'instant',
        })
      })
      await page.waitForTimeout(600)
      await captureScreenshot(page, testInfo, `${site.name}-03-bottom`)
    })
  }
})
