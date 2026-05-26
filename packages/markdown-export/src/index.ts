/**
 * @module @portfolio/markdown-export
 * @description Convierte el HTML rendered de cada pagina del dist a Markdown
 *   y escribe un `.md` gemelo al lado del `index.html`. Pensado para correr
 *   como postbuild (despues de `astro build`), antes del deploy a Cloudflare
 *   Pages. Los agentes que envien `Accept: text/markdown` reciben el `.md`
 *   gemelo via Transform Rule.
 */

export { bundlePagesFunction } from './lib/bundle-pages-function'
export { extractMainContent } from './lib/extract-main-content'
export { htmlToMarkdown } from './lib/html-to-markdown'
export { postbuildExport } from './lib/postbuild-export'
