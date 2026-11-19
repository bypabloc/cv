/**
 * @function GET en/[guide].md
 * @description Version Markdown de una guia en en (`/en/<slug>.md`),
 *   enlazada desde llms.txt (convencion llmstxt.org).
 */
import type { APIRoute, GetStaticPaths } from 'astro'
import {
  GUIDE_SLUGS,
  type GuideSlug,
  guideMarkdown,
  loadGuide,
} from '../../lib/guides'
import { pathFor } from '../../lib/i18n'

export const getStaticPaths = (() =>
  GUIDE_SLUGS.map((guide) => ({ params: { guide } }))) satisfies GetStaticPaths

export const GET: APIRoute = async ({ params, site }) => {
  const slug = params.guide as GuideSlug
  const origin = site?.href.replace(/\/$/, '') ?? ''
  const guide = await loadGuide('en', slug)
  return new Response(guideMarkdown(guide, `${origin}${pathFor('en', slug)}`), {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  })
}
