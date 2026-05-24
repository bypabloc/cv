/**
 * @description Tests para buildHeaders. CSP connect-src debe incluir solo
 *   el API del env, NO los 3 (prod+dev+stage).
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
    expect(out).not.toContain('https://api.portfolio.stage.the-full-stack.com')
  })

  it('Given apiEndpoint stage When build Then connect-src incluye solo el host stage', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.stage.the-full-stack.com',
    })
    expect(out).toContain('https://api.portfolio.stage.the-full-stack.com')
    expect(out).not.toMatch(/https:\/\/api\.portfolio\.the-full-stack\.com[^.]/)
    expect(out).not.toContain('https://api.portfolio.dev.the-full-stack.com')
  })

  it('Given apiEndpoint prod When build Then connect-src incluye solo el host prod', () => {
    const out = buildHeaders({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })
    expect(out).toContain('https://api.portfolio.the-full-stack.com')
    expect(out).not.toContain('https://api.portfolio.dev.the-full-stack.com')
    expect(out).not.toContain('https://api.portfolio.stage.the-full-stack.com')
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
})
