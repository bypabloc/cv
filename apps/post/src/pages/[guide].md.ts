/**
 * @function GET [guide].md
 * @description Version Markdown de una guia en es (`/<slug>.md`), enlazada
 *   desde llms.txt (convencion llmstxt.org).
 */
import type { APIRoute, GetStaticPaths } from 'astro'
import {
  GUIDE_SLUGS,
  type GuideSlug,
  guideMarkdown,
  loadGuide,
} from '../lib/guides'
import { pathFor } from '../lib/i18n'

export const getStaticPaths = (() =>
  GUIDE_SLUGS.map((guide) => ({ params: { guide } }))) satisfies GetStaticPaths

export const GET: APIRoute = async ({ params, site }) => {
  const slug = params.guide as GuideSlug
  const origin = site?.href.replace(/\/$/, '') ?? ''
  const guide = await loadGuide('es', slug)
  return new Response(guideMarkdown(guide, `${origin}${pathFor('es', slug)}`), {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  })
}
