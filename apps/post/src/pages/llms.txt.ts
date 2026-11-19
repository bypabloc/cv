/**
 * @function GET llms.txt
 * @description Indice llmstxt.org de post: una entrada por guia y locale.
 */
import type { APIRoute } from 'astro'
import { LOCALES, loadGuides } from '../lib/guides'
import { mdPathFor, UI } from '../lib/i18n'

export const GET: APIRoute = async ({ site }) => {
  const origin = site?.href.replace(/\/$/, '') ?? ''
  const sections = await Promise.all(
    LOCALES.map(async (locale) => {
      const guides = await loadGuides(locale)
      return [
        `## Posts (${locale})`,
        '',
        ...guides.map(
          (g) =>
            `- [${g.title}](${origin}${mdPathFor(locale, g.slug)}): ${g.description}`,
        ),
        '',
      ].join('\n')
    }),
  )
  const body = [
    '# post · the-full-stack',
    '',
    `> ${UI.en.homeDescription}`,
    '',
    ...sections,
    '## Optional',
    '',
    `- [Full content](${origin}/llms-full.txt): every guide (es and en) in a single markdown file`,
    '',
  ].join('\n')
  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
