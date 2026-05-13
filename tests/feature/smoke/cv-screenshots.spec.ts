/**
 * @feature CV screenshots - portfolio multi-niche multi-viewport
 * @description Captura screenshots de hero + secciones de los 6 sitios
 *   del portfolio post-redisenio mobile-first. Output en results/<niche>/<viewport>/.
 *
 *   3 viewports x 6 apps x 3 scrolls = 54 screenshots.
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

const VIEWPORTS = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 800 },
] as const

test.describe('Feature: CV screenshots - 6 niches x 3 viewports', () => {
  // El spec controla viewports internamente: skip todos los projects excepto
  // desktop-chromium para evitar duplicar ejecucion x5 projects.
  // biome-ignore lint/correctness/noEmptyPattern: Playwright beforeEach requires destructuring pattern as first arg even when no fixtures used
  test.beforeEach(({}, testInfo) => {
    test.skip(
      testInfo.project.name !== 'desktop-chromium',
      'Spec controla viewport internamente; corre solo en desktop-chromium',
    )
  })

  // fullPage screenshots en paginas largas (CV) pueden exceder 15s default
  test.setTimeout(90_000)

  for (const viewport of VIEWPORTS) {
    test.describe(`Viewport: ${viewport.name} (${viewport.width}x${viewport.height})`, () => {
      test.use({
        viewport: { width: viewport.width, height: viewport.height },
      })

      for (const site of SITES) {
        test(`When visito ${site.name} en ${viewport.name} Then el hero renderiza sin overflow horizontal y captura screenshots`, async ({
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

          // Verificar que no hay scroll horizontal: scrollWidth <= viewport.width + margen
          const scrollInfo = await page.evaluate(() => ({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
          }))
          expect(scrollInfo.scrollWidth).toBeLessThanOrEqual(
            scrollInfo.clientWidth + 1,
          )

          // capturar hero (top)
          await captureScreenshot(
            page,
            testInfo,
            `${site.name}-${viewport.name}-01-hero`,
          )

          // scroll a 50% (mid) y capturar
          await page.evaluate(() => {
            window.scrollTo({
              top: window.innerHeight * 1.5,
              behavior: 'instant',
            })
          })
          await page.waitForTimeout(600)
          await captureScreenshot(
            page,
            testInfo,
            `${site.name}-${viewport.name}-02-mid`,
          )

          // scroll al final
          await page.evaluate(() => {
            window.scrollTo({
              top: document.body.scrollHeight,
              behavior: 'instant',
            })
          })
          await page.waitForTimeout(600)
          await captureScreenshot(
            page,
            testInfo,
            `${site.name}-${viewport.name}-03-bottom`,
          )
        })
      }
    })
  }
})
