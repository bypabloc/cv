/**
 * @feature Admin login (flujo REAL contra el backend dev)
 * @description Llena el form de login, hace submit, y valida la respuesta
 *   REAL del Lambda auth (api.portfolio.dev). El Turnstile se bypasea en
 *   modo E2E (NEXT_PUBLIC_E2E_BYPASS) + el bypass token Ed25519 firmado va
 *   en el header X-Turnstile-Bypass-Token (inyectado en window por el
 *   fixture installBypass). El backend dev acepta el bypass con
 *   cf_turnstile_response vacio.
 *
 *   Cubre AC-8, AC-9, AC-49 del plan a-admin + el contrato FLAT del backend
 *   (el bug que daba INVALID_EVENT_DATA al enviar {operation,action,data}).
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

  test('Given un email NO registrado When envio el form de login Then el backend dev responde 404 y muestra "Registrate"', async ({
    page,
  }, testInfo) => {
    test.skip(!hasBypass, 'sin clave privada de bypass (E2E_BYPASS_TOKEN)')
    // WebKit headless en el container no completa el fetch HTTPS cross-origin
    // al backend dev (preflight CORS). El request SI sale (lo valida el spec
    // de shape FLAT en TODOS los browsers); el flujo-completo con respuesta
    // real se cubre en chromium + en api_e2e (server-to-server).
    test.skip(
      testInfo.project.name.includes('webkit'),
      'webkit-en-container no completa el fetch HTTPS cross-origin al backend',
    )

    // Arrange: inyecta el bypass token antes de cargar la page
    await installBypass(page)
    await page.goto(`${ADMIN}/login/`, { waitUntil: 'domcontentloaded' })

    // Email garantizado-inexistente (no spamea: dominio simulator de SES)
    const ghost = `e2e-ghost-${Date.now()}@simulator.amazonses.com`

    // Espera la hidratacion: el submit se habilita cuando el TurnstileWidget
    // E2E emite el token (useEffect). Sin esto, fill() corre antes de que
    // react-hook-form enganche el onChange y el valor se pierde.
    const submit = page.getByTestId('login-submit')
    await expect(submit).toBeEnabled({ timeout: 15_000 })

    // Act: llena el email (blur para forzar el commit en react-hook-form) y
    // envia. El submit dispara login.start contra el backend dev real.
    const emailInput = page.getByTestId('login-email')
    await emailInput.fill(ghost)
    await emailInput.blur()
    await expect(emailInput).toHaveValue(ghost)
    await submit.click()

    // Assert: se valida el EFECTO OBSERVABLE en la UI (no se intercepta la
    // respuesta cross-origin: webkit en Playwright no emite el evento
    // `response` de forma confiable para requests con preflight CORS). Si la
    // UI reacciona con el Alert, el backend respondio 404 EMAIL_NOT_FOUND
    // (con suggest_register) y el contrato FLAT funciono (un 400
    // INVALID_EVENT_DATA NO setearia suggest_register -> sin Alert).
    await expect(
      page.getByRole('alert').filter({ hasText: /no esta registrado/i }),
    ).toBeVisible({ timeout: 30_000 })
    await expect(
      page.getByRole('button', { name: /registrate/i }),
    ).toBeVisible()
  })

  test('Given el form de login When el request sale Then es FLAT y lleva el header de bypass (no 400 INVALID_EVENT_DATA)', async ({
    page,
  }) => {
    test.skip(!hasBypass, 'sin clave privada de bypass (E2E_BYPASS_TOKEN)')

    // Arrange
    await installBypass(page)
    await page.goto(`${ADMIN}/login/`, { waitUntil: 'domcontentloaded' })

    const submit = page.getByTestId('login-submit')
    await expect(submit).toBeEnabled({ timeout: 15_000 })

    // Act: capturo el request crudo para verificar el shape FLAT
    const emailInput = page.getByTestId('login-email')
    await emailInput.fill('shape-check@simulator.amazonses.com')
    await emailInput.blur()
    await expect(emailInput).toHaveValue('shape-check@simulator.amazonses.com')
    const [request] = await Promise.all([
      page.waitForRequest(
        (r) => r.url().includes('/auth') && r.method() === 'POST',
      ),
      page.getByTestId('login-submit').click(),
    ])

    // Assert: el body es FLAT (operation/action/email al nivel raiz, SIN
    // anidar en `data`) y lleva el header de bypass.
    const payload = request.postDataJSON() as Record<string, unknown>
    expect(payload.operation).toBe('login')
    expect(payload.action).toBe('start')
    expect(payload.email).toBe('shape-check@simulator.amazonses.com')
    expect(payload.data, 'el body NO debe anidar `data`').toBeUndefined()
    expect(
      request.headers()['x-turnstile-bypass-token'],
      'falta el header de bypass',
    ).toBe(BYPASS_TOKEN)
  })
})
