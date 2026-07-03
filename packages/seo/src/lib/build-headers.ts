/**
 * @module build-headers
 * @description Genera el contenido del archivo `_headers` (Cloudflare Pages
 *   custom headers) con CSP `connect-src` por env: solo incluye el
 *   hostname del API del env correspondiente, en vez de listar los 3
 *   (prod/dev) como antes.
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
 * @param {boolean} [opts.allowBlobWorkers] - agrega `worker-src 'self' blob:`
 *   a la CSP. Sin la directiva, los Web Workers caen a `default-src 'self'`
 *   y un worker creado desde Blob URL queda bloqueado. Lo necesita journey:
 *   troika-three-text (drei Text) tipografia en un worker via Blob.
 * @returns {string} Contenido completo del archivo `_headers` listo para
 *   escribirse a `public/_headers`.
 *
 * @example
 *   buildHeaders({ apiEndpoint: 'https://api.portfolio.dev.the-full-stack.com' })
 *   // CSP connect-src incluye solo ese hostname (NO prod)
 */
export function buildHeaders(opts: {
  apiEndpoint: string
  allowBlobWorkers?: boolean
}): string {
  const apiOrigin = parseOrigin(opts.apiEndpoint)
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com https://static.cloudflareinsights.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    `connect-src 'self' https://challenges.cloudflare.com ${apiOrigin}`,
    ...(opts.allowBlobWorkers ? ["worker-src 'self' blob:"] : []),
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
    '  Link: </.well-known/mcp/server-card.json>; rel="mcp-server-card"; type="application/json"',
    '',
    // Content-Type para los .md generados por el postbuild markdown-export.
    // El middleware functions/_middleware.ts hace la negociacion via
    // Accept: text/markdown -> reescribe a /<path>/index.md y este header
    // asegura el MIME correcto cuando el .md se sirve directo o reescrito.
    '/*.md',
    '  Content-Type: text/markdown; charset=UTF-8',
    '',
    // Los bloques /.well-known/api-catalog{,.json} y
    // /.well-known/mcp/server-card.json se removieron en el plan
    // ai-audit-level-4. Cloudflare Pages excluye dotdirs del upload,
    // por lo que esos archivos NO estaban en el deploy y el _headers
    // aplicaba el Content-Type al SPA fallback (cuerpo HTML).
    // Ahora los sirven Pages Functions en
    // apps/<niche>/functions/.well-known/*.ts con sus propios headers.
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
