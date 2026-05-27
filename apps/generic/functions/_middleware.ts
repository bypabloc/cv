/**
 * @function _middleware
 * @description Pages Function middleware que intercepta requests con
 *   header `Accept: text/markdown` y devuelve el .md gemelo de la
 *   pagina solicitada. Reemplaza la Cloudflare Transform Rule manual.
 *
 *   Generado por `@portfolio/markdown-export` (buildMarkdownMiddleware).
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
    mdPath = `${original}index.md`
  } else if (original.endsWith('.md')) {
    mdPath = original
  } else {
    mdPath = `${original}/index.md`
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
