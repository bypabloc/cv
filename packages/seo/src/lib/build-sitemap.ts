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

/** Crawlers de IA que se permiten explicitamente en prod (GEO white-hat). */
const AI_CRAWLERS = [
  'GPTBot',
  'OAI-SearchBot',
  'ChatGPT-User',
  'ClaudeBot',
  'Claude-Web',
  'Google-Extended',
  'PerplexityBot',
  'CCBot',
] as const

/**
 * @function isNonProdHost
 * @description Detecta si un siteUrl corresponde a un entorno no productivo
 *   (dev / local). Esos entornos NO deben indexarse. El guard de `.stage.`
 *   se conserva como defensa generica ante cualquier host con label de
 *   entorno intermedio, aunque el entorno stage ya no exista.
 *
 * @param {string} siteUrl - URL absoluta del sitio
 * @returns {boolean} true si el host es dev/localhost/pages.dev
 *
 * @example
 *   isNonProdHost('https://portfolio.dev.the-full-stack.com')  // true
 *   isNonProdHost('http://hub.localhost:9970')                 // true
 *   isNonProdHost('https://the-full-stack.com')                // false
 */
export function isNonProdHost(siteUrl: string): boolean {
  let host: string
  try {
    host = new URL(siteUrl).hostname
  } catch {
    host = siteUrl
  }
  return (
    host === 'localhost' ||
    host.endsWith('.localhost') ||
    host.endsWith('.pages.dev') ||
    host.includes('.dev.') ||
    host.includes('.stage.')
  )
}

/**
 * @function buildRobotsTxt
 * @description Genera /robots.txt segun el entorno del siteUrl.
 *
 *   - Prod: indexable. Permite `*` + lista explicita de crawlers de IA
 *     (GPTBot, ClaudeBot, Google-Extended, PerplexityBot, CCBot...) para
 *     maximizar GEO. Apunta a los sitemaps.
 *   - dev / localhost / pages.dev: `Disallow: /` total. Evita que
 *     Google y los crawlers de IA indexen entornos no productivos.
 *
 * @param {string} siteUrl - URL absoluta del sitio (define el entorno)
 * @returns {string} contenido de robots.txt
 *
 * @example
 *   buildRobotsTxt('https://the-full-stack.com')        // indexable + AI crawlers
 *   buildRobotsTxt('https://portfolio.dev.the-full-stack.com')  // Disallow: /
 */
export function buildRobotsTxt(siteUrl: string): string {
  if (isNonProdHost(siteUrl)) {
    return 'User-agent: *\nDisallow: /\n'
  }

  const u = siteUrl.replace(/\/$/, '')
  const lines: string[] = []

  for (const crawler of AI_CRAWLERS) {
    lines.push(`User-agent: ${crawler}`)
    lines.push('Allow: /')
    lines.push('')
  }

  lines.push('User-agent: *')
  lines.push('Allow: /')
  lines.push('Disallow:')
  lines.push('')
  lines.push(`Sitemap: ${u}/sitemap.xml`)
  lines.push(`Sitemap: ${u}/sitemap-index.xml`)
  lines.push('')

  return lines.join('\n')
}
