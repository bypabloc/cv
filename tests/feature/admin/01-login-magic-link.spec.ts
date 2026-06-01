/**
 * @feature Admin login con magic link / code
 * @description Verifica que el admin sirve la page /login y que el form de
 *   login renderiza (email + Turnstile). El flujo completo de envio de
 *   magic-link corre contra MSW (NEXT_PUBLIC_USE_MSW=true en el dev server).
 *
 *   Cubre AC-8, AC-9, AC-49 del plan a-admin.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin login', () => {
  test('Given el admin When abro /login Then la page responde 2xx y muestra el form', async ({
    page,
  }) => {
    // Act
    const response = await page.goto(`${ADMIN}/login/`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    expect(response, 'sin respuesta de /login').not.toBeNull()
    expect(response?.status(), 'status de /login').toBeLessThan(400)
    await expect(
      page.getByRole('heading', { name: /iniciar sesion/i }),
    ).toBeVisible()
    await expect(
      page.getByRole('textbox', { name: 'Email', exact: true }),
    ).toBeVisible()
  })

  test('Given /login When inspecciono el link a registro Then apunta a /register', async ({
    page,
  }) => {
    // Act
    await page.goto(`${ADMIN}/login/`, { waitUntil: 'domcontentloaded' })
    const href = await page
      .getByRole('link', { name: /registrate/i })
      .getAttribute('href')

    // Assert
    expect(href).toContain('/register')
  })
})
