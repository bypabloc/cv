/**
 * @description Tests para buildSitemap y buildRobotsTxt.
 */
import { describe, expect, it } from 'vitest'
import { buildRobotsTxt, buildSitemap } from '../../src/lib/build-sitemap'

describe('buildSitemap', () => {
  it('Given a basic entry When build Then returns valid XML', () => {
    const xml = buildSitemap([
      {
        loc: 'https://x.example/',
        lastmod: '2026-05-13',
        changefreq: 'weekly',
        priority: 1.0,
      },
    ])
    expect(xml).toMatch(/^<\?xml version="1.0" encoding="UTF-8"\?>/u)
    expect(xml).toContain('<loc>https://x.example/</loc>')
    expect(xml).toContain('<lastmod>2026-05-13</lastmod>')
    expect(xml).toContain('<changefreq>weekly</changefreq>')
    expect(xml).toContain('<priority>1.0</priority>')
  })

  it('Given hreflang alternates When build Then includes xhtml:link', () => {
    const xml = buildSitemap([
      {
        loc: 'https://x.example/',
        alternates: [
          { hreflang: 'es', href: 'https://x.example/' },
          { hreflang: 'en', href: 'https://x.example/en/' },
        ],
      },
    ])
    expect(xml).toContain('xmlns:xhtml="http://www.w3.org/1999/xhtml"')
    expect(xml).toContain(
      '<xhtml:link rel="alternate" hreflang="es" href="https://x.example/"/>',
    )
    expect(xml).toContain(
      '<xhtml:link rel="alternate" hreflang="en" href="https://x.example/en/"/>',
    )
  })

  it('Given URLs with special chars When build Then escapes them', () => {
    const xml = buildSitemap([{ loc: 'https://x.example/?q=a&b=c' }])
    expect(xml).toContain('https://x.example/?q=a&amp;b=c')
  })

  it('Given empty entries When build Then returns valid empty urlset', () => {
    const xml = buildSitemap([])
    expect(xml).toContain('<urlset')
    expect(xml).toContain('</urlset>')
    expect(xml).not.toContain('<url>')
  })
})

describe('buildRobotsTxt', () => {
  it('Given a prod site URL When build Then returns valid robots.txt with sitemap', () => {
    const txt = buildRobotsTxt('https://the-full-stack.com/')
    expect(txt).toContain('User-agent: *')
    expect(txt).toContain('Allow: /')
    expect(txt).toContain('Sitemap: https://the-full-stack.com/sitemap.xml')
    expect(txt).toContain(
      'Sitemap: https://the-full-stack.com/sitemap-index.xml',
    )
  })

  it('Given URL without trailing slash When build Then strips correctly', () => {
    const txt = buildRobotsTxt('https://the-full-stack.com')
    expect(txt).toContain('Sitemap: https://the-full-stack.com/sitemap.xml')
  })

  it('Given a prod URL When build Then allows AI crawlers explicitly', () => {
    const txt = buildRobotsTxt('https://the-full-stack.com')
    expect(txt).toContain('User-agent: GPTBot')
    expect(txt).toContain('User-agent: ClaudeBot')
    expect(txt).toContain('User-agent: Google-Extended')
    expect(txt).toContain('User-agent: PerplexityBot')
  })

  it('Given a dev hostname When build Then disallows all crawlers', () => {
    const txt = buildRobotsTxt('https://portfolio.dev.the-full-stack.com')
    expect(txt).toBe('User-agent: *\nDisallow: /\n')
  })

  it('Given a non-prod intermediate-label host When build Then disallows all crawlers', () => {
    // El guard generico de label de entorno intermedio (.stage.) se
    // conserva como defensa aunque el entorno stage ya no exista.
    const txt = buildRobotsTxt(
      'https://fintech.portfolio.stage.the-full-stack.com',
    )
    expect(txt).toBe('User-agent: *\nDisallow: /\n')
  })

  it('Given a localhost URL When build Then disallows all crawlers', () => {
    const txt = buildRobotsTxt('http://hub.localhost:9970')
    expect(txt).toBe('User-agent: *\nDisallow: /\n')
  })

  it('Given a prod niche URL When build Then is indexable', () => {
    const txt = buildRobotsTxt('https://fintech.portfolio.the-full-stack.com')
    expect(txt).toContain('Disallow:\n')
    expect(txt).not.toContain('Disallow: /\n')
  })
})
