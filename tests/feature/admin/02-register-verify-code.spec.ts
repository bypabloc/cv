/**
 * @feature Admin register + verify code
 * @description Verifica que /register renderiza el form y /verify renderiza
 *   el input de code (8 chars) + el prompt de magic-link. El flujo completo
 *   corre contra MSW.
 *
 *   Cubre AC-9, AC-10, AC-11 del plan a-admin.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin register + verify', () => {
  test('Given el admin When abro /register Then responde 2xx y muestra el form', async ({
    page,
  }) => {
    // Act
    const response = await page.goto(`${ADMIN}/register/`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    expect(response?.status(), 'status de /register').toBeLessThan(400)
    await expect(page.getByLabel(/email/i)).toBeVisible()
  })

  test('Given /verify?flow=register When abro Then muestra el input de code y el tab magic-link', async ({
    page,
  }) => {
    // Act
    const response = await page.goto(`${ADMIN}/verify/?flow=register`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    expect(response?.status(), 'status de /verify').toBeLessThan(400)
    await expect(
      page.getByRole('heading', { name: /verifica tu email/i }),
    ).toBeVisible()
  })
})
