import type { APIRequestContext } from '@playwright/test'

/**
 * @class ApiClient
 * @description Cliente HTTP reusable para llamadas al backend desde tests E2E.
 *   Stub minimo: el portfolio actual no tiene backend. Cuando se agregue
 *   (form de contacto, analytics, etc.), agregar metodos aqui.
 */
export class ApiClient {
  private readonly request: APIRequestContext

  constructor(opts: { request: APIRequestContext }) {
    this.request = opts.request
  }

  /**
   * Health check generico contra cualquier URL.
   *
   * @returns true si responde 2xx en el timeout default
   */
  async isUp(url: string): Promise<boolean> {
    try {
      const response = await this.request.get(url, { timeout: 5_000 })
      return response.ok()
    } catch {
      return false
    }
  }
}
