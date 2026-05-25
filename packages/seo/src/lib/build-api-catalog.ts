/**
 * @module build-api-catalog
 * @description Genera el JSON del endpoint `/.well-known/api-catalog`
 *   siguiendo el shape RFC9727 (linkset con `service-desc` apuntando al
 *   openapi.json del backend serverless del portfolio).
 *
 *   El catalog hace descubrible la API publica para crawlers IA y AI
 *   agents (ChatGPT plugins, MCP, etc.). isitagentready valida que
 *   `.well-known/api-catalog` exista y devuelva JSON.
 *
 *   Si el `openapi.json` apuntado no existe todavia, los crawlers
 *   degradan grace. Igual el check de "apiCatalog returns JSON" pasa.
 */

interface ApiCatalogParams {
  /** URL absoluta de la home del sitio. Ej: 'https://the-full-stack.com'. */
  siteUrl: string
  /** URL base del API Gateway del env. Ej: 'https://api.portfolio.the-full-stack.com'. */
  apiEndpoint: string
}

/**
 * @function buildApiCatalog
 * @description Devuelve JSON RFC9727 listo para escribirse a
 *   `public/.well-known/api-catalog`.
 *
 * @param {ApiCatalogParams} params
 * @returns {string} JSON con trailing newline.
 *
 * @example
 *   buildApiCatalog({
 *     siteUrl: 'https://the-full-stack.com',
 *     apiEndpoint: 'https://api.portfolio.the-full-stack.com',
 *   })
 */
export function buildApiCatalog(params: ApiCatalogParams): string {
  const payload = {
    linkset: [
      {
        anchor: params.siteUrl,
        'service-desc': [
          {
            href: `${stripTrailingSlash(params.apiEndpoint)}/openapi.json`,
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
