/**
 * @feature Admin login (flujo REAL contra el backend dev)
 * @description Llena el form de login, hace submit, y valida la respuesta
 *   REAL del Lambda auth (api.portfolio.dev). El Turnstile se bypasea en
 *   modo E2E (NEXT_PUBLIC_E2E_BYPASS) + el bypass token Ed25519 firmado va
 *   en el header X-Turnstile-Bypass-Token (inyectado en window por el
 *   fixture installBypass). El backend dev acepta el bypass con
 *   cf_turnstile_response vacio.
 *
 *   Login UNIFICADO (plan admin-security-overview, bloque D): el primer
 *   request del login es `login.check-email` (no `login.start`). Si el email
 *   no existe, la UI ofrece crear la cuenta (login.start la crea); ya NO hay
 *   un flujo `/register` separado ni un link "Registrate".
 */
import {
  BYPASS_TOKEN,
  expect,
  hasBypass,
  installBypass,
  subdomainUrl,
  test,
} from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin login (flujo real)', () => {
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
    await expect(page.getByTestId('login-email')).toBeVisible()
  })

  test('Given /login When inspecciono la page Then NO hay link a /register (fusion register->login)', async ({
    page,
  }) => {
    // Act
    await page.goto(`${ADMIN}/login/`, { waitUntil: 'domcontentloaded' })

    // Assert: la operation register se fusiono en login -> ya no existe la
    // ruta /register ni un link "Registrate". El registro ocurre dentro del
    // propio login (login.start crea el user si el email no existe).
    await expect(page.getByRole('link', { name: /registrate/i })).toHaveCount(0)
  })

  test('Given el form de login When el primer request sale Then es FLAT, action=check-email y lleva el header de bypass', async ({
    page,
  }) => {
    test.skip(!hasBypass, 'sin clave privada de bypass (E2E_BYPASS_TOKEN)')

    // Arrange
    await installBypass(page)
    await page.goto(`${ADMIN}/login/`, { waitUntil: 'domcontentloaded' })

    const submit = page.getByTestId('login-submit')
    await expect(submit).toBeEnabled({ timeout: 15_000 })

    // Act: capturo el request crudo para verificar el shape FLAT. El primer
    // paso del login unificado es `login.check-email`.
    const emailInput = page.getByTestId('login-email')
    await emailInput.fill('shape-check@simulator.amazonses.com')
    await emailInput.blur()
    await expect(emailInput).toHaveValue('shape-check@simulator.amazonses.com')
    const [request] = await Promise.all([
      page.waitForRequest(
        (r) => r.url().includes('/auth') && r.method() === 'POST',
      ),
      submit.click(),
    ])

    // Assert: el body es FLAT (operation/action/email al nivel raiz, SIN
    // anidar en `data`) y lleva el header de bypass. action = check-email.
    const payload = request.postDataJSON() as Record<string, unknown>
    expect(payload.operation).toBe('login')
    expect(payload.action).toBe('check-email')
    expect(payload.email).toBe('shape-check@simulator.amazonses.com')
    expect(payload.data, 'el body NO debe anidar `data`').toBeUndefined()
    expect(
      request.headers()['x-turnstile-bypass-token'],
      'falta el header de bypass',
    ).toBe(BYPASS_TOKEN)
  })
})
