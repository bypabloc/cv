/**
 * @function buildSitemap
 * @description Genera sitemap.xml. Astro tiene @astrojs/sitemap pero esto
 *   permite generarlo manualmente para casos custom (hub multi-site).
 *
 *   Soporta hreflang alternates por locale.
 */
interface SitemapEntry {
  loc: string
  lastmod?: string
  changefreq?:
    | 'always'
    | 'hourly'
    | 'daily'
    | 'weekly'
    | 'monthly'
    | 'yearly'
    | 'never'
  priority?: number
  alternates?: Array<{ hreflang: string; href: string }>
}

export function buildSitemap(entries: SitemapEntry[]): string {
  const lines: string[] = []
  lines.push('<?xml version="1.0" encoding="UTF-8"?>')
  lines.push(
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
  )
  for (const entry of entries) {
    lines.push('  <url>')
    lines.push(`    <loc>${escapeXml(entry.loc)}</loc>`)
    if (entry.lastmod) lines.push(`    <lastmod>${entry.lastmod}</lastmod>`)
    if (entry.changefreq)
      lines.push(`    <changefreq>${entry.changefreq}</changefreq>`)
    if (entry.priority !== undefined)
      lines.push(`    <priority>${entry.priority.toFixed(1)}</priority>`)
    if (entry.alternates) {
      for (const alt of entry.alternates) {
        lines.push(
          `    <xhtml:link rel="alternate" hreflang="${escapeXml(alt.hreflang)}" href="${escapeXml(alt.href)}"/>`,
        )
      }
    }
    lines.push('  </url>')
  }
  lines.push('</urlset>')
  return `${lines.join('\n')}\n`
}

function escapeXml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

/**
 * @function buildRobotsTxt
 * @description Genera /robots.txt.
 */
export function buildRobotsTxt(siteUrl: string): string {
  const u = siteUrl.replace(/\/$/, '')
  return [
    'User-agent: *',
    'Allow: /',
    '',
    `Sitemap: ${u}/sitemap.xml`,
    `Sitemap: ${u}/sitemap-index.xml`,
    '',
  ].join('\n')
}
