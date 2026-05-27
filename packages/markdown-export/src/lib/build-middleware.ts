/**
 * @module build-middleware
 * @description Genera el contenido TypeScript de la Pages Function
 *   `functions/_middleware.ts` que hace content negotiation para
 *   `Accept: text/markdown`.
 *
 *   Reemplaza la Cloudflare Transform Rule TR-1 (que era activacion
 *   manual en el dashboard). Reasons:
 *   - Versionado en git (rastreable, code-reviewable).
 *   - Cero pasos manuales post-deploy.
 *   - Free tier de Pages Functions (100k req/dia, mas que suficiente).
 *
 *   Logica del middleware:
 *   1. Si la request no es GET o no incluye Accept: text/markdown -> next().
 *   2. Calcula el path del .md gemelo:
 *      - `/` -> `/index.md`
 *      - `/about` o `/about/` -> `/about/index.md`
 *      - `/en` -> `/en/index.md`
 *   3. Hace fetch interno via env.ASSETS.fetch.
 *   4. Si el .md existe (200) -> lo devuelve. Si no, pasa al siguiente
 *      handler (no rompe la request original).
 *
 *   Compartido entre 6 niches via codegen para evitar copy/paste manual.
 */

/**
 * @function buildMarkdownMiddleware
 * @description Devuelve el contenido textual de `_middleware.ts` listo
 *   para escribirse en `apps/<niche>/functions/_middleware.ts`.
 *
 * @returns {string} TypeScript source con onRequest handler.
 *
 * @example
 *   buildMarkdownMiddleware()
 *   // 'export const onRequest = async (...): Promise<Response> => { ... }'
 */
export function buildMarkdownMiddleware(): string {
  return `/**
 * @function _middleware
 * @description Pages Function middleware que intercepta requests con
 *   header \`Accept: text/markdown\` y devuelve el .md gemelo de la
 *   pagina solicitada. Reemplaza la Cloudflare Transform Rule manual.
 *
 *   Generado por \`@portfolio/markdown-export\` (buildMarkdownMiddleware).
 *   NO editar a mano — regenerar via postbuild si cambian las reglas.
 */
interface EventContext {
  request: Request
  env: { ASSETS: { fetch: (request: Request) => Promise<Response> } }
  next: () => Promise<Response>
}

export const onRequest = async (context: EventContext): Promise<Response> => {
  const { request, env, next } = context

  if (request.method !== 'GET') {
    return next()
  }

  const accept = request.headers.get('accept') ?? ''
  if (!accept.toLowerCase().includes('text/markdown')) {
    return next()
  }

  const url = new URL(request.url)
  const original = url.pathname
  let mdPath: string
  if (original === '/' || original === '') {
    mdPath = '/index.md'
  } else if (original.endsWith('/')) {
    mdPath = \`\${original}index.md\`
  } else if (original.endsWith('.md')) {
    mdPath = original
  } else {
    mdPath = \`\${original}/index.md\`
  }

  url.pathname = mdPath
  const mdRequest = new Request(url.toString(), {
    method: 'GET',
    headers: request.headers,
  })

  try {
    const mdResponse = await env.ASSETS.fetch(mdRequest)
    if (mdResponse.ok) {
      return new Response(mdResponse.body, {
        status: 200,
        headers: {
          'content-type': 'text/markdown; charset=UTF-8',
          'cache-control': 'public, max-age=3600',
          vary: 'Accept',
        },
      })
    }
  } catch {
    // env.ASSETS no disponible o fallo: pasa al siguiente handler
  }

  return next()
}
`
}
