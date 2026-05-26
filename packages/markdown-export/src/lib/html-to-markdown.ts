/**
 * @module html-to-markdown
 * @description Convierte HTML a Markdown usando `turndown` + plugin GFM
 *   (tablas, strikethrough, task lists). Configurado para producir un
 *   Markdown legible por agentes (ATX headings, fenced code blocks,
 *   bullets con `-`).
 *
 *   NO descarta `<script>`/`<style>`/`<noscript>`/`<iframe>`/`<svg>`
 *   manualmente: turndown ya los elimina por defecto en la serializacion
 *   (no hay regla que los convierta). Si en el futuro algun bot resuelve
 *   ese contenido, agregar reglas custom via `td.addRule`.
 */
import TurndownService from 'turndown'
// @ts-expect-error turndown-plugin-gfm no expone tipos oficiales en 2026.
import { gfm } from 'turndown-plugin-gfm'

interface ConvertParams {
  /** HTML fuente. Puede ser un fragmento o un documento completo. */
  html: string
}

/**
 * @function htmlToMarkdown
 * @description Convierte HTML a Markdown listo para servir a agentes.
 *
 * @example
 *   htmlToMarkdown({ html: '<h1>Pablo</h1><p>Lorem</p>' })
 *   // "# Pablo\n\nLorem\n"
 */
export function htmlToMarkdown(params: ConvertParams): string {
  const td = new TurndownService({
    headingStyle: 'atx',
    codeBlockStyle: 'fenced',
    bulletListMarker: '-',
    emDelimiter: '_',
    strongDelimiter: '**',
    linkStyle: 'inlined',
  })
  td.use(gfm)
  // Filtros explicitos (defensa en profundidad: si el HTML viene con
  // script/style inline, los borramos antes de convertir). Tipado como
  // unknown[] porque turndown declara `Filter` mas amplio que
  // `keyof HTMLElementTagNameMap` (acepta 'svg', 'iframe', etc).
  td.remove(['script', 'style', 'noscript', 'iframe', 'svg'] as never)
  const md = td.turndown(params.html).trim()
  return md.length === 0 ? '' : `${md}\n`
}
