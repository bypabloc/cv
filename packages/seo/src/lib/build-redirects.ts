/**
 * @module build-redirects
 * @description Genera el contenido del archivo `_redirects` (Cloudflare
 *   Pages). Reglas activas:
 *
 *   1. `/sitemap.xml` -> `/sitemap-index.xml` (301): compat con crawlers
 *      que chequean el path canonico cuando Astro genera el sitemap como
 *      index.
 *   2. `/.well-known/api-catalog` -> `/.well-known/api-catalog.json`
 *      (200 = rewrite interno): el archivo real se publica con extension
 *      `.json` para evitar el SPA fallback de Cloudflare Pages (que
 *      devuelve `index.html` para rutas sin extension reconocida). El
 *      rewrite 200 mantiene la URL canonica RFC 9727 sirviendo el JSON.
 *
 *   Sintaxis de Cloudflare Pages _redirects:
 *     <from> <to> <status>
 *   Una regla por linea. 301 = redirect permanente, 200 = rewrite interno.
 */

/**
 * @function buildRedirects
 * @description Devuelve el contenido textual de `_redirects` listo para
 *   escribirse a `public/_redirects`.
 *
 * @returns {string} Contenido completo del archivo.
 *
 * @example
 *   buildRedirects()
 *   // "/sitemap.xml /sitemap-index.xml 301\n
 *   //  /.well-known/api-catalog /.well-known/api-catalog.json 200\n"
 */
export function buildRedirects(): string {
  return [
    '/sitemap.xml /sitemap-index.xml 301',
    '/.well-known/api-catalog /.well-known/api-catalog.json 200',
    '',
  ].join('\n')
}
