/**
 * @function POST /mcp
 * @description Cloudflare Pages Function que expone el MCP server del
 *   portfolio (Model Context Protocol via JSON-RPC 2.0). Wrapper thin
 *   que delega a `@portfolio/mcp` (codigo compartido entre los 6 niches).
 *
 *   Los datos del CV vienen de `./_data/cv-snapshot.json` (generado en
 *   build por `packages/mcp/scripts/build-snapshot.mjs` y escrito por
 *   `scripts/postbuild-functions.mjs`). NO se importa `@portfolio/content`
 *   en runtime: ese paquete usa `import.meta.glob` (Vite-only) y el
 *   runtime de Cloudflare Workers no lo implementa.
 *
 *   Se bundlea con esbuild en el postbuild a `dist/functions/mcp.js`.
 *   Wrangler la recoge automaticamente al hacer `pages deploy dist`.
 */

import type { CvSnapshot } from '@portfolio/mcp'
import { createSnapshotProvider, handleRequest } from '@portfolio/mcp'
import snapshot from './_data/cv-snapshot.json'

interface PagesContext {
  request: Request
}

const dataProvider = createSnapshotProvider(snapshot as unknown as CvSnapshot)

export const onRequestPost = async (ctx: PagesContext): Promise<Response> => {
  const body = await ctx.request.text()
  const response = await handleRequest(body, dataProvider)
  return new Response(JSON.stringify(response), {
    status: 200,
    headers: {
      'content-type': 'application/json; charset=UTF-8',
      'access-control-allow-origin': '*',
      'cache-control': 'no-store',
    },
  })
}

export const onRequestOptions = (): Response => {
  return new Response(null, {
    status: 204,
    headers: {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'POST, OPTIONS',
      'access-control-allow-headers': 'content-type',
      'access-control-max-age': '86400',
    },
  })
}

export const onRequestGet = (): Response => {
  return new Response(
    JSON.stringify({
      jsonrpc: '2.0',
      id: null,
      error: { code: -32600, message: 'GET not supported. Use POST.' },
    }),
    {
      status: 405,
      headers: {
        'content-type': 'application/json; charset=UTF-8',
        allow: 'POST, OPTIONS',
      },
    },
  )
}
