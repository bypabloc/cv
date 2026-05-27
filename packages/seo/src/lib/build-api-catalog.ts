/**
 * @module build-api-catalog
 * @description Genera el JSON del endpoint `/.well-known/api-catalog.json`
 *   siguiendo el shape RFC9727 (linkset con `service-desc` apuntando al
 *   `openapi.json` del portfolio).
 *
 *   El catalog hace descubrible la API publica para crawlers IA y AI
 *   agents (ChatGPT plugins, MCP, etc.). isitagentready valida que
 *   el .well-known/api-catalog devuelva JSON valido + que el
 *   service-desc[].href resuelva a un OpenAPI 3.x valido.
 *
 *   En el plan ai-audit-level-4 el openapi.json se sirve desde el MISMO
 *   origen del portfolio (`{siteUrl}/openapi.json`), no desde el API
 *   Gateway del backend (que NO lo expone). Esto evita el broken link
 *   que reportaba isitagentready.
 */

interface ApiCatalogParams {
  /** URL absoluta de la home del sitio. Ej: 'https://the-full-stack.com'. */
  siteUrl: string
  /**
   * URL base del API Gateway del env. Ej: 'https://api.portfolio.the-full-stack.com'.
   * Hoy NO se usa para el linkset (el openapi.json esta en {siteUrl}/openapi.json
   * porque el backend no lo expone). Se mantiene en la firma por compat con
   * los callers ya escritos.
   */
  apiEndpoint?: string
}

/**
 * @function buildApiCatalog
 * @description Devuelve JSON RFC9727 listo para que la Pages Function
 *   `apps/<niche>/functions/.well-known/api-catalog.json.ts` lo sirva.
 *
 * @param {ApiCatalogParams} params
 * @returns {string} JSON con trailing newline.
 *
 * @example
 *   buildApiCatalog({ siteUrl: 'https://the-full-stack.com' })
 *   // service-desc[].href -> 'https://the-full-stack.com/openapi.json'
 */
export function buildApiCatalog(params: ApiCatalogParams): string {
  const base = stripTrailingSlash(params.siteUrl)
  const payload = {
    linkset: [
      {
        anchor: base,
        'service-desc': [
          {
            href: `${base}/openapi.json`,
            type: 'application/json',
          },
        ],
      },
    ],
  }
  return `${JSON.stringify(payload, null, 2)}\n`
}

function stripTrailingSlash(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url
}
