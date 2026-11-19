/**
 * @function GET llms-full.txt
 * @description Todas las guias de post (es y en) completas en un solo
 *   Markdown (llmstxt.org).
 */
import type { APIRoute } from 'astro'
import { guideMarkdown, LOCALES, loadGuides } from '../lib/guides'
import { pathFor } from '../lib/i18n'

export const GET: APIRoute = async ({ site }) => {
  const origin = site?.href.replace(/\/$/, '') ?? ''
  const guides = (await Promise.all(LOCALES.map(loadGuides))).flat()
  const body = guides
    .map((g) => {
      const url = `${origin}${pathFor(g.locale, g.slug)}`
      return `Source: ${url}\n\n${guideMarkdown(g, url).trim()}`
    })
    .join('\n\n---\n\n')
  return new Response(`${body}\n`, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
