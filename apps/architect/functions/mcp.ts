/**
 * @function POST /mcp
 * @description Cloudflare Pages Function que expone el MCP server del
 *   portfolio (Model Context Protocol via JSON-RPC 2.0). Wrapper thin
 *   que delega a `@portfolio/mcp` (codigo compartido entre los 6 niches).
 *
 *   Se bundlea con esbuild en el postbuild (apps/<niche>/scripts/
 *   postbuild-functions.mjs) a `dist/functions/mcp.js`. Wrangler la
 *   recoge automaticamente al hacer `pages deploy dist`.
 */
import { handleRequest } from '@portfolio/mcp'

interface PagesContext {
  request: Request
}

export const onRequestPost = async (ctx: PagesContext): Promise<Response> => {
  const body = await ctx.request.text()
  const response = await handleRequest(body)
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
