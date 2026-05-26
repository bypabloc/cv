/**
 * @module extract-main-content
 * @description Aisla el contenido "principal" de un HTML rendered antes
 *   de convertirlo a Markdown. Prefiere `<main>`, despues `<article>`,
 *   finalmente `<body>`. Elimina `nav`, `footer`, `aside` y elementos
 *   `.tracking-pixel` para que el `.md` sea solo el contenido legible
 *   por agentes (sin chrome repetitivo).
 *
 *   Razon: el `.md` que vamos a servir como respuesta del Transform Rule
 *   debe ser conciso. Incluir el header/nav/footer en cada pagina
 *   contamina la respuesta y aumenta el token count del agente.
 */
import { parse } from 'node-html-parser'

const STRIP_SELECTORS = [
  'nav',
  'footer',
  'aside',
  '.tracking-pixel',
  '[data-tracking]',
  // script/style ya los borra turndown, pero por defensa los quitamos aqui:
  'script',
  'style',
  'noscript',
]

/**
 * @function extractMainContent
 * @description Devuelve el `innerHTML` del contenedor principal de la
 *   pagina (preferentemente `<main>`), sin chrome.
 *
 * @example
 *   extractMainContent(
 *     '<body><nav>NAV</nav><main><h1>T</h1></main><footer>F</footer></body>'
 *   )
 *   // '<h1>T</h1>'
 */
export function extractMainContent(html: string): string {
  const root = parse(html)
  const main =
    root.querySelector('main') ??
    root.querySelector('article') ??
    root.querySelector('body') ??
    root
  for (const sel of STRIP_SELECTORS) {
    for (const node of main.querySelectorAll(sel)) {
      node.remove()
    }
  }
  return main.innerHTML
}
