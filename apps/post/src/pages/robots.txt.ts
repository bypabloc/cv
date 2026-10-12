/**
 * @function GET robots.txt
 * @description dev (`*.dev.*`) bloquea todo; prod permite todo, incluidos
 *   los crawlers de IA (GEO), y declara el sitemap.
 */
import type { APIRoute } from 'astro'

export const GET: APIRoute = ({ site }) => {
  const origin = site?.href.replace(/\/$/, '') ?? ''
  const body = origin.includes('.dev.')
    ? 'User-agent: *\nDisallow: /\n'
    : [
        'User-agent: *',
        'Allow: /',
        '',
        ...[
          'GPTBot',
          'ClaudeBot',
          'PerplexityBot',
          'Google-Extended',
          'CCBot',
        ].flatMap((bot) => [`User-agent: ${bot}`, 'Allow: /', '']),
        `Sitemap: ${origin}/sitemap-index.xml`,
        '',
      ].join('\n')
  return new Response(body, { headers: { 'Content-Type': 'text/plain' } })
}
