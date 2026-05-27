/**
 * @function GET /.well-known/api-catalog.json
 * @description Cloudflare Pages Function que sirve el linkset RFC 9727
 *   del catalogo de API del portfolio. Reemplaza el asset estatico
 *   `dist/.well-known/api-catalog.json` que Pages NO uploadea porque
 *   `.well-known/` es un dotdir (regla de dotfiles del upload).
 *
 *   El JSON viene de `./_data/api-catalog.json` (generado en build por
 *   `scripts/postbuild-functions.mjs` que invoca `buildApiCatalog` de
 *   `@portfolio/seo`).
 */
import payload from '../_data/api-catalog.json'

export const onRequestGet = (): Response => {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: {
      'content-type': 'application/linkset+json; charset=UTF-8',
      'access-control-allow-origin': '*',
      'cache-control': 'public, max-age=3600',
    },
  })
}
