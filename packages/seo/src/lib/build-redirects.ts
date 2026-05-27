/**
 * @module build-redirects
 * @description Genera el contenido del archivo `_redirects` (Cloudflare
 *   Pages). Reglas activas:
 *
 *   1. `/sitemap.xml` -> `/sitemap-index.xml` (301): compat con crawlers
 *      que chequean el path canonico cuando Astro genera el sitemap como
 *      index.
 *
 *   Sintaxis de Cloudflare Pages _redirects:
 *     <from> <to> <status>
 *   Una regla por linea. 301 = redirect permanente, 200 = rewrite interno.
 *
 *   Historico: en plan ai-audit-level-3-4 hubo una regla
 *   `/.well-known/api-catalog -> /.well-known/api-catalog.json 200` para
 *   evitar el SPA fallback. Se eliminó en ai-audit-level-4: los archivos
 *   en `.well-known/` NO se uploadean (regla de dotfiles), por lo que el
 *   target del rewrite tampoco existia. Ahora los `.well-known/*` los
 *   sirven Pages Functions en `apps/<niche>/functions/.well-known/*.ts`.
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
  return ['/sitemap.xml /sitemap-index.xml 301', ''].join('\n')
}
