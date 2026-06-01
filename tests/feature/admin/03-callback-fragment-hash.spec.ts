/**
 * @feature Admin magic-link callback (fragment hash)
 * @description El callback decodifica el fragment hash (#access=&refresh=&...),
 *   guarda los tokens, limpia el URL con history.replaceState y redirige al
 *   area protegida. Sin fragment -> redirige a /login.
 *
 *   Cubre AC-12, AC-13 del plan a-admin.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

test.describe('Feature: Admin callback fragment hash', () => {
  test('Given /auth/callback SIN fragment When carga Then redirige a /login', async ({
    page,
  }) => {
    // Act
    await page.goto(`${ADMIN}/callback/`, { waitUntil: 'domcontentloaded' })
    await page.waitForURL(/\/login/, { timeout: 15_000 })

    // Assert
    expect(page.url()).toContain('/login')
  })

  test('Given /auth/callback con fragment invalido When carga Then redirige a /login (no rompe)', async ({
    page,
  }) => {
    // Act
    await page.goto(`${ADMIN}/callback/#access=&refresh=`, {
      waitUntil: 'domcontentloaded',
    })
    await page.waitForURL(/\/login/, { timeout: 15_000 })

    // Assert
    expect(page.url()).toContain('/login')
  })
})
