/**
 * @module build-redirects
 * @description Genera el contenido del archivo `_redirects` (Cloudflare
 *   Pages). Hoy solo redirige `/sitemap.xml` -> `/sitemap-index.xml` para
 *   compat con crawlers IA que chequean el path canonico (isitagentready,
 *   AI bots) cuando Astro genera el sitemap como index.
 *
 *   Sintaxis de Cloudflare Pages _redirects:
 *     <from> <to> <status>
 *   Una regla por linea, status 301 para redirect permanente.
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
 *   // "/sitemap.xml /sitemap-index.xml 301\n"
 */
export function buildRedirects(): string {
  return '/sitemap.xml /sitemap-index.xml 301\n'
}
