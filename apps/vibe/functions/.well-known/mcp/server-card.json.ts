/**
 * @function GET /.well-known/mcp/server-card.json
 * @description Cloudflare Pages Function que sirve el MCP server card
 *   (Model Context Protocol descriptor) del portfolio. Reemplaza el
 *   asset estatico `dist/.well-known/mcp/server-card.json` que Pages
 *   NO uploadea porque `.well-known/` es un dotdir.
 *
 *   El JSON viene de `../../_data/mcp-server-card.json` (generado en build
 *   por `scripts/postbuild-functions.mjs` que invoca `buildMcpServerCard`
 *   de `@portfolio/seo`).
 */
import payload from '../../_data/mcp-server-card.json'

export const onRequestGet = (): Response => {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: {
      'content-type': 'application/json; charset=UTF-8',
      'access-control-allow-origin': '*',
      'cache-control': 'public, max-age=3600',
    },
  })
}
