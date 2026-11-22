/**
 * @module llms-full
 * @description Arma `llms-full.txt` de un locale: cada guia completa con una
 *   cabecera unica por articulo (URL, idioma, fechas, autor y version en el
 *   otro idioma), para que un LLM separe los articulos sin ambiguedad.
 */
import { guideMarkdown, LOCALES, type Locale, loadGuides } from './guides'
import { AUTHOR, pathFor } from './i18n'

/** Marca de inicio de articulo: no aparece en el contenido de las guias. */
export const ARTICLE_MARK = '<!-- article -->'

/**
 * @function llmsFull
 * @description Todas las guias de `locale` en un solo Markdown.
 * @example await llmsFull('en', 'https://post.the-full-stack.com')
 */
export async function llmsFull(
  locale: Locale,
  origin: string,
): Promise<string> {
  const other = LOCALES.find((l) => l !== locale) ?? locale
  const guides = await loadGuides(locale)
  const body = guides
    .map((g) => {
      const url = `${origin}${pathFor(locale, g.slug)}`
      return [
        ARTICLE_MARK,
        `URL: ${url}`,
        `Lang: ${locale}`,
        `Published: ${g.published}`,
        `Updated: ${g.updated}`,
        `Author: ${AUTHOR}`,
        `Alternate: ${origin}${pathFor(other, g.slug)} (${other})`,
        '',
        guideMarkdown(g, url).trim(),
      ].join('\n')
    })
    .join('\n\n---\n\n')
  return `${body}\n`
}
