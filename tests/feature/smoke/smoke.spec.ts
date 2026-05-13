/**
 * @feature Smoke tests - portfolio multi-subdominio
 * @description Verifica que cada uno de los 6 subdominios del stack
 *   local responde HTTP 200 y renderiza al menos el body. Es el smoke
 *   minimo que prueba: nginx + cada app Astro + reverse-proxy.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const SUBDOMAINS = [
  { name: 'generic (apex)', host: undefined },
  { name: 'hub', host: 'hub' },
  { name: 'fintech', host: 'fintech' },
  { name: 'architect', host: 'architect' },
  { name: 'leader', host: 'leader' },
  { name: 'vibe', host: 'vibe' },
] as const

test.describe('Feature: Smoke - 6 apps Astro responden', () => {
  for (const { name, host } of SUBDOMAINS) {
    test(`Given el stack local levantado When abro ${name} Then carga sin error`, async ({
      page,
    }) => {
      // Arrange
      const url = subdomainUrl(host)

      // Act
      const response = await page.goto(`${url}/`, {
        waitUntil: 'domcontentloaded',
      })

      // Assert: HTTP 2xx
      expect(response, `no response from ${url}`).not.toBeNull()
      expect(response?.status(), `status del primer load`).toBeLessThan(400)

      // Assert: el body renderizo (no es pagina de error)
      const body = page.locator('body')
      await expect(body).toBeVisible()
    })
  }

  test('Given services.localhost When la abro Then aparece "Servicios del portfolio"', async ({
    page,
  }) => {
    const url = subdomainUrl('services')
    await page.goto(`${url}/`, { waitUntil: 'domcontentloaded' })

    await expect(page.locator('h1')).toContainText(/servicios/i)
  })
})
