/**
 * @feature Smoke tests - hub cards apuntan al subdominio del env activo
 * @description Verifica que las 5 cards del hub.localhost generan hrefs
 *   absolutos al subdominio del env actual (ej. http://fintech.localhost:9970
 *   en local) y que el click lleva al sitio correspondiente sin error.
 *
 *   Cubre AC-5 y AC-6 del plan (env-driven site URLs).
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const NICHE_CARDS = [
  { niche: 'fintech', host: 'fintech' },
  { niche: 'architect', host: 'architect' },
  { niche: 'leader', host: 'leader' },
  { niche: 'vibe', host: 'vibe' },
  { niche: 'generic', host: undefined },
] as const

test.describe('Feature: Hub cards - URLs derivadas del env activo', () => {
  test('Given hub abierto When inspecciono las cards Then hay 5 anchors con data-niche [AC-5]', async ({
    page,
  }) => {
    // Arrange
    const hubUrl = subdomainUrl('hub')

    // Act
    await page.goto(`${hubUrl}/`, { waitUntil: 'domcontentloaded' })
    const cards = page.locator('a.hub-card[data-niche]')

    // Assert
    await expect(cards).toHaveCount(5)
  })

  for (const { niche, host } of NICHE_CARDS) {
    test(`Given hub abierto When leo href de card[data-niche=${niche}] Then apunta al subdominio del env activo [AC-5]`, async ({
      page,
    }) => {
      // Arrange
      const hubUrl = subdomainUrl('hub')
      const expectedUrl = subdomainUrl(host)

      // Act
      await page.goto(`${hubUrl}/`, { waitUntil: 'domcontentloaded' })
      const href = await page
        .locator(`a.hub-card[data-niche="${niche}"]`)
        .getAttribute('href')

      // Assert
      expect(href, `card[${niche}] sin href`).not.toBeNull()
      expect(href).toBe(expectedUrl)
    })
  }

  test('Given hub abierto When click en card[data-niche=fintech] Then aterriza en fintech.localhost con HTTP 2xx [AC-6]', async ({
    page,
  }) => {
    // Arrange
    const hubUrl = subdomainUrl('hub')
    const expectedFintech = subdomainUrl('fintech')

    // Act
    await page.goto(`${hubUrl}/`, { waitUntil: 'domcontentloaded' })
    const fintechCard = page.locator('a.hub-card[data-niche="fintech"]')
    const [response] = await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
      fintechCard.click(),
    ])

    // Assert
    expect(response, 'sin respuesta tras click').not.toBeNull()
    expect(response?.status(), 'status del navegacion').toBeLessThan(400)
    expect(page.url()).toContain(expectedFintech)
  })
})
