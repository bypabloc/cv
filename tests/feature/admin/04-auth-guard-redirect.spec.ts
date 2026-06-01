/**
 * @feature Admin AuthGuard redirect
 * @description Una ruta protegida sin sesion redirige a /login?next=<path>.
 *
 *   Cubre AC-19, AC-20 del plan a-admin.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

const ADMIN = subdomainUrl('admin')

const PROTECTED = ['/settings', '/sessions', '/users'] as const

test.describe('Feature: Admin AuthGuard', () => {
  for (const path of PROTECTED) {
    test(`Given sin sesion When accedo a ${path} Then redirige a /login con next`, async ({
      page,
    }) => {
      // Act
      await page.goto(`${ADMIN}${path}/`, { waitUntil: 'domcontentloaded' })
      await page.waitForURL(/\/login\/?\?next=/, { timeout: 15_000 })

      // Assert
      expect(page.url()).toContain('next=')
      expect(decodeURIComponent(page.url())).toContain(path)
    })
  }
})
