/**
 * @feature Contact form (React 18 + Zod) - flujo completo E2E
 * @description Cubre:
 *   1. Validacion Zod en cliente (errors per-field).
 *   2. Happy path con bypass de Turnstile (POST real al Lambda dev).
 *   3. Persistencia: tras enviar, recargar -> card visible.
 *   4. Boton "Enviar otro mensaje" limpia storage y re-muestra el form.
 *   5. Errores del backend (mock 400/429) renderizan correctamente.
 *
 * Bypass de Turnstile:
 *   - Solo se activa si TURNSTILE_BYPASS_SECRET env var esta presente.
 *   - El secret se inyecta a la pagina via `addInitScript` -> window.
 *   - El frontend lee `window.__playwrightTurnstileBypass`, agrega header
 *     `X-Turnstile-Bypass-Secret`, y envia cf_token vacio.
 *   - El Lambda (en stage=dev) detecta cf_token vacio + secret matchea SSM
 *     param `/portfolio/dev/turnstile-bypass-secret` -> skip Cloudflare API.
 */
import type { Page } from '@playwright/test'
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const BYPASS_SECRET = process.env.TURNSTILE_BYPASS_SECRET ?? ''

/**
 * Navega a /contact y espera a que el React island se hidrate. El form usa
 * `client:load` pero la hidratacion puede tardar ~200-500ms despues de
 * `domcontentloaded`. Esperar al input[name=name] garantiza estado interactivo.
 */
async function gotoContactReady(page: Page): Promise<void> {
  await page.goto(`${subdomainUrl()}/contact`, {
    waitUntil: 'domcontentloaded',
  })
  await expect(page.getByTestId('contact-form')).toBeVisible()
  await expect(page.locator('input[name="name"]')).toBeVisible()
}

test.describe('Feature: Contact form (React 18 + Zod)', () => {
  test.beforeEach(async ({ page }) => {
    // Inyectar bypass token ANTES de cargar la pagina. La inyeccion ocurre
    // en cada navegacion (incluso reloads) por el contrato de addInitScript.
    if (BYPASS_SECRET) {
      await page.addInitScript((secret: string) => {
        ;(
          window as Window & { __playwrightTurnstileBypass?: string }
        ).__playwrightTurnstileBypass = secret
      }, BYPASS_SECRET)
    }
  })

  test('Given form vacio When submit Then muestra errores Zod en name/email/message', async ({
    page,
  }) => {
    await gotoContactReady(page)

    await page.getByTestId('contact-submit').click()

    await expect(page.getByTestId('error-name')).toHaveText(
      /Minimo 2 caracteres/i,
    )
    await expect(page.getByTestId('error-email')).toHaveText(
      /email es obligatorio/i,
    )
    await expect(page.getByTestId('error-message')).toHaveText(
      /Minimo 10 caracteres/i,
    )
  })

  test('Given email invalido When blur Then error de formato; al corregir desaparece', async ({
    page,
  }) => {
    await gotoContactReady(page)

    const emailInput = page.locator('input[name="email"]')
    await emailInput.fill('no-es-email')
    await emailInput.blur()
    await expect(page.getByTestId('error-email')).toHaveText(
      /Email invalido. Revisa el formato/i,
    )

    await emailInput.fill('pacg1991@gmail.com')
    // Mientras tipea con error activo, debe re-validar y limpiar
    await expect(page.getByTestId('error-email')).toBeHidden()
  })

  // -----------------------------------------------------------------
  // Happy path + persistencia: requiere bypass secret real para que el
  // Lambda dev acepte la peticion. Se skipea si no esta seteado.
  // -----------------------------------------------------------------
  test.describe('with Turnstile bypass (skipped if TURNSTILE_BYPASS_SECRET not set)', () => {
    test.skip(
      !BYPASS_SECRET,
      'TURNSTILE_BYPASS_SECRET no esta seteada en el entorno',
    )

    test('Given API responde 400 con errores per-field When submit Then pintan errores del backend', async ({
      page,
    }) => {
      // Solo intercepta el POST al API Gateway. NO uses '**/contact' a secas
      // porque tambien matchea la navegacion a `/contact` (HTML).
      await page.route(
        /https:\/\/[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com\/[a-z]+\/contact$/,
        async (route) => {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Validation failed',
              code: 'INVALID_INPUT',
              extra: {
                errors: [
                  {
                    type: 'string_too_short',
                    loc: ['body', 'message'],
                    msg: 'Field too short',
                    ctx: { min_length: 10 },
                  },
                ],
              },
            }),
          })
        },
      )

      await gotoContactReady(page)
      await page.locator('input[name="name"]').fill('Pablo Test')
      await page.locator('input[name="email"]').fill('pacg1991@gmail.com')
      await page
        .locator('textarea[name="message"]')
        .fill('Mensaje suficientemente largo para pasar Zod cliente.')

      await page.getByTestId('contact-submit').click()

      await expect(page.getByTestId('error-message')).toHaveText(
        /Minimo 10 caracteres/i,
      )
      await expect(page.getByTestId('contact-status')).toHaveAttribute(
        'data-kind',
        'error',
      )
    })

    test('Given API responde 429 When submit Then mensaje de rate limit', async ({
      page,
    }) => {
      await page.route(
        /https:\/\/[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com\/[a-z]+\/contact$/,
        async (route) => {
          await route.fulfill({
            status: 429,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Too many requests',
              code: 'RATE_LIMITED',
            }),
          })
        },
      )

      await gotoContactReady(page)
      await page.locator('input[name="name"]').fill('Pablo Test')
      await page.locator('input[name="email"]').fill('pacg1991@gmail.com')
      await page
        .locator('textarea[name="message"]')
        .fill('Mensaje suficientemente largo para pasar Zod cliente.')

      await page.getByTestId('contact-submit').click()

      await expect(page.getByTestId('contact-status')).toContainText(
        /Demasiados intentos/i,
      )
    })

    test('Given form valido When submit con bypass Then 202 + card de confirmacion', async ({
      page,
    }) => {
      await gotoContactReady(page)
      const uniqueMsg = `[E2E test] ${new Date().toISOString()} - mensaje suficientemente largo.`
      await page.locator('input[name="name"]').fill('Playwright Test')
      await page.locator('input[name="email"]').fill('pacg1991@gmail.com')
      await page.locator('textarea[name="message"]').fill(uniqueMsg)

      // Capturar la response al backend para verificar status 202 (modo
      // async actual; el encoder publica a SQS y el worker procesa
      // despues).
      const responsePromise = page.waitForResponse(
        (res) =>
          res.url().includes('/contact') && res.request().method() === 'POST',
      )
      await page.getByTestId('contact-submit').click()
      const response = await responsePromise
      expect(response.status()).toBe(202)
      const body = (await response.json()) as { contact_id: string }
      expect(body.contact_id).toMatch(/^[0-9a-f-]{36}$/i)

      // El card aparece
      await expect(page.getByTestId('contact-sent-card')).toBeVisible()
      await expect(page.getByTestId('contact-sent-id')).toHaveText(
        body.contact_id,
      )
    })

    test('Given mensaje enviado When recargo Then card sigue visible (localStorage)', async ({
      page,
    }) => {
      // Simular estado previo: setear localStorage directo con un record valido
      await gotoContactReady(page)
      const future = Date.now() + 7 * 24 * 60 * 60 * 1000
      await page.evaluate(
        (record) => {
          window.localStorage.setItem('contact_sent', JSON.stringify(record))
        },
        {
          contactId: '019e28fc-b97d-7d79-91a5-44c9b19465b4',
          sentAt: Date.now(),
          expiresAt: future,
        },
      )

      await page.reload({ waitUntil: 'domcontentloaded' })

      await expect(page.getByTestId('contact-sent-card')).toBeVisible()
      await expect(page.getByTestId('contact-sent-id')).toHaveText(
        '019e28fc-b97d-7d79-91a5-44c9b19465b4',
      )
      await expect(page.getByTestId('contact-form')).toBeHidden()
    })

    test('Given card visible When click "Enviar otro mensaje" Then form vuelve a aparecer', async ({
      page,
    }) => {
      await gotoContactReady(page)
      const future = Date.now() + 7 * 24 * 60 * 60 * 1000
      await page.evaluate(
        (record) => {
          window.localStorage.setItem('contact_sent', JSON.stringify(record))
        },
        {
          contactId: 'test-resend-id',
          sentAt: Date.now(),
          expiresAt: future,
        },
      )
      await page.reload({ waitUntil: 'domcontentloaded' })

      await expect(page.getByTestId('contact-sent-card')).toBeVisible()
      await page.getByTestId('contact-resend-btn').click()

      await expect(page.getByTestId('contact-form')).toBeVisible()
      await expect(page.getByTestId('contact-sent-card')).toBeHidden()

      const stored = await page.evaluate(() =>
        window.localStorage.getItem('contact_sent'),
      )
      expect(stored).toBe(null)
    })
  })
})
