/**
 * @description Tests para buildHeaders. CSP connect-src debe incluir solo
 *   el API del env, NO los 2 (prod+dev). Los bloques de
 *   .well-known/*.json se removieron en ai-audit-level-4 (los sirven
 *   Pages Functions con sus propios headers).
 */
import { describe, expect, it } from 'vitest'

import { buildHeaders } from '../../src/lib/build-headers'

describe('buildHeaders', () => {
  it('Given apiEndpoint dev When build Then connect-src incluye solo el host dev', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.dev.the-full-stack.com',
    })
    expect(out).toContain(
      "connect-src 'self' https://challenges.cloudflare.com https://api.portfolio.dev.the-full-stack.com",
    )
    expect(out).not.toContain('https://api.portfolio.the-full-stack.com ')
  })

  it('Given apiEndpoint prod When build Then connect-src incluye solo el host prod', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })
    expect(out).toContain('https://api.portfolio.the-full-stack.com')
    expect(out).not.toContain('https://api.portfolio.dev.the-full-stack.com')
  })

  it('Given URL con path When build Then descarta el path y queda solo el origen', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.dev.the-full-stack.com/contact',
    })
    expect(out).toContain('https://api.portfolio.dev.the-full-stack.com;')
    expect(out).not.toContain('/contact')
  })

  it('Given apiEndpoint http (no https) When build Then throws', () => {
    expect(() =>
      buildHeaders({ apiEndpoint: 'http://api.example.com' }),
    ).toThrow(/debe ser https/)
  })

  it('Given apiEndpoint invalido When build Then throws', () => {
    expect(() => buildHeaders({ apiEndpoint: 'no-es-url' })).toThrow(
      /apiEndpoint invalido/,
    )
  })

  it('Given build When inspecciono Then incluye headers estaticos esperados', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.dev.the-full-stack.com',
    })
    expect(out).toMatch(/^\/\*\n/)
    expect(out).toContain('Strict-Transport-Security: max-age=63072000')
    expect(out).toContain('X-Content-Type-Options: nosniff')
    expect(out).toContain('Referrer-Policy: strict-origin-when-cross-origin')
    expect(out).toContain('Permissions-Policy: camera=()')
    expect(out).toContain('X-Frame-Options: DENY')
    expect(out).toContain("default-src 'self'")
    expect(out).toContain("frame-ancestors 'none'")
  })

  it('Given build When inspecciono Then incluye 4 directivas Link para crawlers IA', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })
    expect(out).toContain('Link: </sitemap-index.xml>; rel="sitemap"')
    expect(out).toContain(
      'Link: </llms.txt>; rel="alternate"; type="text/plain"; title="llms.txt"',
    )
    expect(out).toContain(
      'Link: </.well-known/api-catalog.json>; rel="api-catalog"; type="application/linkset+json"',
    )
    expect(out).toContain(
      'Link: </.well-known/mcp/server-card.json>; rel="mcp-server-card"; type="application/json"',
    )
  })

  it('Given build When inspecciono Then NO incluye bloques Content-Type para api-catalog (los sirven Functions)', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })
    // Las URLs canonicas las atiende Pages Functions con sus headers propios.
    expect(out).not.toMatch(/\n\/\.well-known\/api-catalog\n/)
    expect(out).not.toMatch(/\n\/\.well-known\/api-catalog\.json\n/)
    expect(out).not.toMatch(/\n\/\.well-known\/mcp\/server-card\.json\n/)
  })

  it('Given allowBlobWorkers When build Then CSP incluye worker-src blob', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
      allowBlobWorkers: true,
    })
    expect(out).toContain("worker-src 'self' blob:")
  })

  it('Given sin allowBlobWorkers When build Then CSP NO incluye worker-src', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })
    expect(out).not.toContain('worker-src')
  })

  it('Given build When inspecciono Then expone Content-Type text/markdown para /*.md', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })
    expect(out).toContain('/*.md\n')
    expect(out).toMatch(
      /\/\*\.md\n\s+Content-Type: text\/markdown; charset=UTF-8/,
    )
  })
})
