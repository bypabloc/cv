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
  it('Given a site URL When build Then returns valid robots.txt with sitemap', () => {
    const txt = buildRobotsTxt('https://x.example/')
    expect(txt).toContain('User-agent: *')
    expect(txt).toContain('Allow: /')
    expect(txt).toContain('Sitemap: https://x.example/sitemap.xml')
    expect(txt).toContain('Sitemap: https://x.example/sitemap-index.xml')
  })

  it('Given URL without trailing slash When build Then strips correctly', () => {
    const txt = buildRobotsTxt('https://x.example')
    expect(txt).toContain('Sitemap: https://x.example/sitemap.xml')
  })
})
