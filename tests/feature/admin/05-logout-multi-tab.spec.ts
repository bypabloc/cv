/**
 * @feature Admin logout + multi-tab sync
 * @description El admin expone el SPA en /; sin sesion AuthGuard redirige a
 *   /login. Este spec valida el punto de entrada del shell protegido y que el
 *   404 SPA fallback funciona (ruta inexistente sirve el SPA).
 *
 *   El logout multi-tab (BroadcastChannel) se cubre a fondo en unit
 *   (use-multi-tab-sync.test). Aqui el smoke E2E del fallback + guard.
 *
 *   Cubre AC-17, AC-18 (smoke), AC-45 del plan a-admin.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin shell entry + SPA fallback', () => {
  test('Given sin sesion When abro / Then AuthGuard redirige a /login', async ({
    page,
  }) => {
    // Act
    await page.goto(`${ADMIN}/`, { waitUntil: 'domcontentloaded' })
    await page.waitForURL(/\/login/, { timeout: 15_000 })

    // Assert
    expect(page.url()).toContain('/login')
  })

  test('Given una ruta dinamica inexistente When la abro Then el SPA fallback sirve la app', async ({
    page,
  }) => {
    // Act: ruta client-side; _redirects (/* /index.html 200) sirve el SPA
    const response = await page.goto(`${ADMIN}/users/?user=usr_inexistente`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    expect(response?.status(), 'el SPA fallback debe servir 2xx').toBeLessThan(
      400,
    )
  })
})
