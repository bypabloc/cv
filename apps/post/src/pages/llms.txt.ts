/**
 * @function GET llms.txt
 * @description Indice llmstxt.org de post: una entrada por guia y locale.
 */
import type { APIRoute } from 'astro'
import { LOCALES, loadGuides } from '../lib/guides'
import { AUTHOR, pathFor, UI } from '../lib/i18n'

export const GET: APIRoute = async ({ site }) => {
  const origin = site?.href.replace(/\/$/, '') ?? ''
  const sections = await Promise.all(
    LOCALES.map(async (locale) => {
      const guides = await loadGuides(locale)
      return [
        `## ${UI[locale].eyebrow} (${locale})`,
        '',
        ...guides.map(
          (g) =>
            `- [${g.title}](${origin}${pathFor(locale, g.slug)}): ${g.description}`,
        ),
        '',
      ].join('\n')
    }),
  )
  const body = [
    '# post · the-full-stack',
    '',
    `> ${UI.en.homeDescription} Author: ${AUTHOR}.`,
    '',
    ...sections,
  ].join('\n')
  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
