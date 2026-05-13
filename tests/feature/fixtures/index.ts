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

export type { Page }
export { expect }
