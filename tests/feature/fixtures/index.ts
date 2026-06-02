import type { Page } from '@playwright/test'
import { test as base, expect } from '@playwright/test'

import { ApiClient } from './api/api-client.js'

/**
 * Portfolio E2E fixtures.
 *
 * El portfolio no tiene backend ni auth: los specs son anonimos. Si en
 * el futuro se agrega API (form de contacto, etc.), `apiClient` se
 * expone para verificaciones contra el backend desde tests.
 *
 * Helpers para URLs por subdominio: `subdomainUrl('hub')` retorna
 * `http://hub.localhost:<PROXY_PORT>` según la baseURL del config.
 */
export interface TestFixtures {
  apiClient: ApiClient
}

export const test = base.extend<TestFixtures>({
  apiClient: async ({ request }, use) => {
    const client = new ApiClient({ request })
    await use(client)
  },
})

/**
 * Genera la URL completa para un subdominio.
 *
 * @example
 *   subdomainUrl('hub')        // "http://hub.localhost:9970"
 *   subdomainUrl('fintech')    // "http://fintech.localhost:9970"
 *   subdomainUrl()             // baseURL (apex, equivalente a apps/generic)
 */
export function subdomainUrl(subdomain?: string): string {
  const port = process.env.PROXY_PORT ?? '9970'
  if (!subdomain) {
    return `http://localhost:${port}`
  }
  return `http://${subdomain}.localhost:${port}`
}

/**
 * Bypass token Ed25519 firmado, inyectado por `test_runner` (feature.py)
 * en la env del container Playwright como `E2E_BYPASS_TOKEN`. El admin lo
 * lee de `window.__E2E_BYPASS_TOKEN__` y lo manda en el header
 * `X-Turnstile-Bypass-Token`. Vacio si no hay clave privada local.
 */
export const BYPASS_TOKEN = process.env.E2E_BYPASS_TOKEN ?? ''

/** true si hay un bypass token disponible para el flujo auth real. */
export const hasBypass = BYPASS_TOKEN.length > 0

/**
 * Inyecta el bypass token en `window.__E2E_BYPASS_TOKEN__` ANTES de que
 * cargue cualquier script de la pagina (addInitScript corre en cada
 * navegacion). Llamar al inicio del test, antes del primer `page.goto`.
 *
 * @example
 *   test.skip(!hasBypass, 'sin clave privada de bypass')
 *   await installBypass(page)
 *   await page.goto(`${ADMIN}/login/`)
 */
export async function installBypass(page: Page): Promise<void> {
  await page.addInitScript((token) => {
    ;(window as { __E2E_BYPASS_TOKEN__?: string }).__E2E_BYPASS_TOKEN__ = token
  }, BYPASS_TOKEN)
}

export type { Page }
export { expect }
