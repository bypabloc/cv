/**
 * @feature Admin sessions-mgmt (mis sesiones de auth)
 * @description /sessions esta protegida por AuthGuard. El flujo autenticado de
 *   listar/revocar sesiones (no la actual -> 400) se cubre a fondo en unit
 *   (features/sessions-mgmt/*) con MSW; aqui el smoke E2E del guard + que la
 *   ruta existe.
 *
 *   NO confundir con la feature `sessions` de METRICAS (tracking de
 *   visitantes), que vive en el plan b-analytics-api.
 *
 *   Cubre AC-37, AC-38 (smoke), AC-19 del plan a-admin.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin sessions-mgmt', () => {
  test('Given sin sesion When abro /sessions Then redirige a /login con next', async ({
    page,
  }) => {
    // Act
    await page.goto(`${ADMIN}/sessions/`, { waitUntil: 'domcontentloaded' })
    await page.waitForURL(/\/login\/?\?next=/, { timeout: 15_000 })

    // Assert
    expect(decodeURIComponent(page.url())).toContain('/sessions')
  })

  test('Given el build When abro /cv Then el placeholder responde 2xx', async ({
    page,
  }) => {
    // Act (cv es publico dentro del shell protegido; smoke del SPA fallback)
    const response = await page.goto(`${ADMIN}/cv/`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    expect(response?.status(), 'status de /cv').toBeLessThan(400)
  })
})
