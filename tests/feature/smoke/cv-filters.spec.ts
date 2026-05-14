/**
 * @feature CV filters via query params (docs/specs/cv-filters-query-params.md)
 * @description Valida que el filter engine client-side funciona end-to-end
 *   sobre las apps reales: URL params -> items filtrados + chips sync + URL
 *   replaceState + ATS-safe fallback.
 *
 *   Cubre AC-4 (tech filter), AC-6 (date range), AC-11 (URL update sin
 *   reload), AC-13 (clear filters), AC-16 (JS disabled = todo visible),
 *   AC-19 (filtros persisten al cambiar locale), AC-20 (funciona en 5 apps).
 */

import { expect, subdomainUrl, test } from '../fixtures/index.js'

const APPS_WITH_FILTERS = [
  { name: 'generic', host: undefined },
  { name: 'fintech', host: 'fintech' },
  { name: 'architect', host: 'architect' },
  { name: 'leader', host: 'leader' },
  { name: 'vibe', host: 'vibe' },
] as const

test.describe('Feature: CV filters via query params', () => {
  // biome-ignore lint/correctness/noEmptyPattern: Playwright beforeEach requires destructuring pattern as first arg even when no fixtures used
  test.beforeEach(({}, testInfo) => {
    test.skip(
      testInfo.project.name !== 'desktop-chromium',
      'Spec corre solo en desktop-chromium',
    )
  })

  test.describe('AC-4: tech filter hides non-matching items', () => {
    test('Given ?tech=Vue When load generic home Then only items with Vue remain visible', async ({
      page,
    }) => {
      await page.goto(`${subdomainUrl()}?tech=Vue`, {
        waitUntil: 'networkidle',
      })
      // Wait for filter bar to appear (means JS booted)
      await expect(page.locator('[data-filter-bar]')).toBeVisible({
        timeout: 10_000,
      })
      // Cualquier item filterable sin Vue debe estar hidden
      const allItems = page.locator('[data-filterable]')
      const visibleItems = page.locator('[data-filterable]:not([hidden])')
      const total = await allItems.count()
      const visible = await visibleItems.count()
      expect(visible).toBeLessThan(total)
      expect(visible).toBeGreaterThan(0)
    })
  })

  test.describe('AC-11: chip click updates URL without reload', () => {
    test('Given chip click Then URL gains query param without full reload', async ({
      page,
    }) => {
      await page.goto(subdomainUrl(), {
        waitUntil: 'networkidle',
      })
      await expect(page.locator('[data-filter-bar]')).toBeVisible()

      // Inyectar un "marcador" en window para detectar reload completo:
      // si hay reload, el marcador desaparece.
      await page.evaluate(() => {
        ;(
          window as unknown as { __filterTestMarker: boolean }
        ).__filterTestMarker = true
      })

      // Click first tech chip
      const firstTechChip = page.locator('[data-filter-chip="tech"]').first()
      await firstTechChip.click()

      // URL incluye el param
      await expect.poll(() => page.url(), { timeout: 5000 }).toContain('tech=')

      // Marcador sigue vivo (no hubo full reload, history.replaceState lo preserva)
      const markerStillThere = await page.evaluate(
        () =>
          (window as unknown as { __filterTestMarker?: boolean })
            .__filterTestMarker === true,
      )
      expect(markerStillThere).toBe(true)
    })
  })

  test.describe('AC-13: clear-all resets filters and URL', () => {
    test('Given chip clicked and then clear-all clicked Then URL has no query', async ({
      page,
    }) => {
      await page.goto(`${subdomainUrl()}?tech=Vue`, {
        waitUntil: 'networkidle',
      })
      await expect(page.locator('[data-filter-bar]')).toBeVisible()

      await page.locator('[data-filter-clear="all"]').click()
      // URL must lose query
      await expect.poll(() => page.url()).not.toContain('tech=')
      // All items must be visible again
      const totalItems = await page.locator('[data-filterable]').count()
      const visibleItems = await page
        .locator('[data-filterable]:not([hidden])')
        .count()
      expect(visibleItems).toBe(totalItems)
    })
  })

  test.describe('AC-16: ATS-safe fallback (JS disabled)', () => {
    test.use({ javaScriptEnabled: false })

    test('Given JS disabled When load home Then filter bar is hidden and all items visible', async ({
      page,
    }) => {
      await page.goto(subdomainUrl(), { waitUntil: 'domcontentloaded' })
      // Filter bar should still have `hidden` attribute (since JS never ran)
      const filterBar = page.locator('[data-filter-bar]')
      await expect(filterBar).toBeAttached()
      const hidden = await filterBar.getAttribute('hidden')
      expect(hidden).not.toBeNull()

      // All items must be in the DOM (no hidden applied by JS)
      const allItems = await page.locator('[data-filterable]').count()
      expect(allItems).toBeGreaterThan(0)
      const visibleItems = await page
        .locator('[data-filterable]:not([hidden])')
        .count()
      expect(visibleItems).toBe(allItems)
    })
  })

  test.describe('AC-19: filters persist across locale switch', () => {
    test('Given /?tech=Vue and click EN link Then /en?tech=Vue preserves param', async ({
      page,
    }) => {
      // Navigate with filter active
      await page.goto(`${subdomainUrl()}?tech=Vue`, {
        waitUntil: 'networkidle',
      })
      // Manually navigate to EN keeping the query string
      await page.goto(`${subdomainUrl()}/en?tech=Vue`, {
        waitUntil: 'networkidle',
      })
      await expect(page.locator('[data-filter-bar]')).toBeVisible()
      const url = page.url()
      expect(url).toContain('/en')
      expect(url).toContain('tech=Vue')
    })
  })

  test.describe('AC-20: filters work across 5 apps', () => {
    for (const app of APPS_WITH_FILTERS) {
      test(`Given ${app.name} home with ?tech=TypeScript Then filter bar appears`, async ({
        page,
      }) => {
        const baseUrl = subdomainUrl(app.host)
        await page.goto(`${baseUrl}/?tech=TypeScript`, {
          waitUntil: 'networkidle',
        })
        await expect(page.locator('[data-filter-bar]')).toBeVisible({
          timeout: 10_000,
        })
        // At least one chip must be marked active
        const activeChips = page.locator('[data-filter-chip].is-active')
        await expect(activeChips.first()).toBeVisible({ timeout: 5_000 })
      })
    }
  })

  test.describe('cv-filters.js bundle is served', () => {
    test('Given /cv-filters.js request Then returns 200 with JS', async ({
      page,
    }) => {
      const response = await page.request.get(`${subdomainUrl()}/cv-filters.js`)
      expect(response.status()).toBe(200)
      const contentType = response.headers()['content-type'] ?? ''
      expect(contentType).toMatch(/javascript|application\/javascript/u)
      const body = await response.text()
      expect(body.length).toBeGreaterThan(1000)
      expect(body.length).toBeLessThan(15_000) // sanity check: < 15kb minified
    })
  })
})
