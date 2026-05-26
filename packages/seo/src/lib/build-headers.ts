/**
 * @module build-headers
 * @description Genera el contenido del archivo `_headers` (Cloudflare Pages
 *   custom headers) con CSP `connect-src` por env: solo incluye el
 *   hostname del API del env correspondiente, en vez de listar los 3
 *   (prod/dev/stage) como antes.
 *
 *   Cloudflare Pages lee `dist/_headers` y aplica las directivas a cada
 *   ruta. Sintaxis: `/*` matchea todo, headers indentados 2 espacios.
 *
 *   El listado de scripts/styles/imgs/fonts es estable; solo `connect-src`
 *   varia por env (depende del API del env). Si en el futuro se agrega
 *   un endpoint nuevo del backend, va en el mismo origen.
 */

/**
 * @function buildHeaders
 * @description Devuelve el contenido textual de `_headers` para una app.
 *
 * @param {object} opts
 * @param {string} opts.apiEndpoint - URL base del API Gateway del env
 *   (sin trailing slash). Ej: `https://api.portfolio.dev.the-full-stack.com`.
 *   Se valida que sea https + sin path para preservar el modelo de
 *   origenes de CSP.
 * @returns {string} Contenido completo del archivo `_headers` listo para
 *   escribirse a `public/_headers`.
 *
 * @example
 *   buildHeaders({ apiEndpoint: 'https://api.portfolio.dev.the-full-stack.com' })
 *   // CSP connect-src incluye solo ese hostname (NO prod ni stage)
 */
export function buildHeaders(opts: { apiEndpoint: string }): string {
  const apiOrigin = parseOrigin(opts.apiEndpoint)
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com https://static.cloudflareinsights.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    `connect-src 'self' https://challenges.cloudflare.com ${apiOrigin}`,
    'frame-src https://challenges.cloudflare.com',
    "object-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
  ].join('; ')

  return [
    '/*',
    '  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload',
    '  X-Content-Type-Options: nosniff',
    '  Referrer-Policy: strict-origin-when-cross-origin',
    '  Permissions-Policy: camera=(), microphone=(), geolocation=()',
    `  Content-Security-Policy: ${csp}`,
    '  X-Frame-Options: DENY',
    '  Link: </sitemap-index.xml>; rel="sitemap"',
    '  Link: </llms.txt>; rel="alternate"; type="text/plain"; title="llms.txt"',
    '  Link: </.well-known/api-catalog.json>; rel="api-catalog"; type="application/linkset+json"',
    '',
    // El archivo real vive en .json para evitar el SPA fallback de
    // Cloudflare Pages (rutas sin extension caen en index.html).
    // Mantenemos tambien el bloque sin extension porque _redirects hace
    // rewrite 200, asi que ambas URLs sirven el mismo body.
    '/.well-known/api-catalog',
    '  Content-Type: application/linkset+json; charset=UTF-8',
    '',
    '/.well-known/api-catalog.json',
    '  Content-Type: application/linkset+json; charset=UTF-8',
    '',
  ].join('\n')
}

/**
 * Extrae el origen (scheme + host) de una URL, descartando path / query.
 * Falla con error claro si la URL no es https o esta malformada — la CSP
 * NO debe quedar con un valor invalido (rompe el browser en silencio).
 */
function parseOrigin(url: string): string {
  let parsed: URL
  try {
    parsed = new URL(url)
  } catch {
    throw new Error(
      `buildHeaders: apiEndpoint invalido (${url}). Esperado URL absoluta tipo https://api.example.com`,
    )
  }
  if (parsed.protocol !== 'https:') {
    throw new Error(
      `buildHeaders: apiEndpoint debe ser https (recibido ${parsed.protocol}//${parsed.host})`,
    )
  }
  return `${parsed.protocol}//${parsed.host}`
}
