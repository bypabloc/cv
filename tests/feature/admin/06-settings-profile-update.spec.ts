/**
 * @feature Admin settings (perfil)
 * @description /settings esta protegida por AuthGuard. Sin sesion redirige a
 *   /login. El flujo autenticado de editar el display_name + cambio de
 *   password + MFA se cubre a fondo en unit (features/settings/*) con MSW y
 *   store controlados; aqui el smoke E2E del guard + que la ruta existe en el
 *   build estatico.
 *
 *   Cubre AC-31, AC-32, AC-33 (smoke), AC-19 del plan a-admin.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin settings', () => {
  test('Given sin sesion When abro /settings Then redirige a /login con next', async ({
    page,
  }) => {
    // Act
    await page.goto(`${ADMIN}/settings/`, { waitUntil: 'domcontentloaded' })
    await page.waitForURL(/\/login\/?\?next=/, { timeout: 15_000 })

    // Assert
    expect(decodeURIComponent(page.url())).toContain('/settings')
  })

  test('Given el build When abro /settings/security Then el SPA fallback responde 2xx', async ({
    page,
  }) => {
    // Act
    const response = await page.goto(`${ADMIN}/settings/security/`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    expect(response?.status(), 'status de /settings/security').toBeLessThan(400)
  })
})
