/**
 * @feature Contact form (React 18 + Zod) - validacion + persistencia E2E
 * @description Cubre lo que el BROWSER puede verificar sin enviar el form:
 *   1. Validacion Zod en cliente (errors per-field).
 *   2. Persistencia: con un record en localStorage, recargar -> card visible.
 *   3. Boton "Enviar otro mensaje" limpia storage y re-muestra el form.
 *
 *   El happy path de ENVIO (POST real al Lambda + 202 + card) NO se prueba
 *   desde el browser: el form exige el widget Turnstile real y ya NO hay
 *   bypass desde el frontend. Ese flujo se cubre server-to-server con el
 *   CLI `api_e2e` (token Ed25519 firmado contra dev/stage).
 */
import type { Page } from '@playwright/test'
import { expect, subdomainUrl, test } from '../fixtures/index.js'

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
  // Persistencia: NO envia el form (setea localStorage directo + reload),
  // asi que no depende del captcha ni del backend.
  // -----------------------------------------------------------------
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
