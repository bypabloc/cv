/**
 * @feature Admin register (flujo REAL contra el backend dev)
 * @description Llena el form de registro con un email sintetico unico, hace
 *   submit, y valida que el Lambda auth (api.portfolio.dev) responde 200 con
 *   un temp_token + la UI navega a /verify?flow=register. El Turnstile se
 *   bypasea en E2E (header X-Turnstile-Bypass-Token + cf_turnstile_response
 *   vacio). Tambien valida /verify render.
 *
 *   Cubre AC-9, AC-10, AC-11 del plan a-admin + el contrato FLAT del backend.
 */
import {
  expect,
  hasBypass,
  installBypass,
  subdomainUrl,
  test,
} from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin register (flujo real)', () => {
  test('Given el admin When abro /register Then responde 2xx y muestra el form', async ({
    page,
  }) => {
    // Act
    const response = await page.goto(`${ADMIN}/register/`, {
      waitUntil: 'domcontentloaded',
    })

    // Assert
    expect(response?.status(), 'status de /register').toBeLessThan(400)
    await expect(page.getByTestId('register-email')).toBeVisible()
  })

  test('Given un email nuevo When envio el form de registro Then el backend dev responde 200 y navega a /verify', async ({
    page,
  }, testInfo) => {
    test.skip(!hasBypass, 'sin clave privada de bypass (E2E_BYPASS_TOKEN)')
    // WebKit headless en el container no completa el fetch HTTPS cross-origin
    // al backend dev (preflight CORS). El flujo-completo se cubre en chromium
    // + en api_e2e (server-to-server). Ver 01-login spec.
    test.skip(
      testInfo.project.name.includes('webkit'),
      'webkit-en-container no completa el fetch HTTPS cross-origin al backend',
    )

    // Arrange
    await installBypass(page)
    await page.goto(`${ADMIN}/register/`, { waitUntil: 'domcontentloaded' })

    // Email sintetico unico (dominio simulator de SES: no envia email real)
    const email = `e2e-reg-${Date.now()}@simulator.amazonses.com`

    // Espera la hidratacion: el submit se habilita cuando el TurnstileWidget
    // E2E emite el token. Sin esto, fill() corre antes de que
    // react-hook-form enganche el onChange y el valor se pierde.
    const submit = page.getByTestId('register-submit')
    await expect(submit).toBeEnabled({ timeout: 15_000 })

    // Act: llena + blur (commit en react-hook-form) + submit. Dispara
    // register.start contra el backend dev real.
    const emailInput = page.getByTestId('register-email')
    await emailInput.fill(email)
    await emailInput.blur()
    await expect(emailInput).toHaveValue(email)
    await submit.click()

    // Assert: el EFECTO OBSERVABLE es la navegacion a /verify?flow=register.
    // El hook useRegisterStart solo navega en onSuccess (register.start 200
    // con temp_token); un 400 INVALID_EVENT_DATA dispararia onError (toast,
    // sin navegacion). Asi se valida el flujo real sin interceptar la
    // respuesta cross-origin (webkit no emite `response` con preflight CORS).
    await page.waitForURL(/\/verify/, { timeout: 30_000 })
    expect(page.url()).toContain('flow=register')
  })

  test('Given /verify?flow=register When abro Then muestra el heading de verificacion', async ({
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
