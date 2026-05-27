/**
 * @description Tests para buildApiCatalog. Genera JSON RFC9727 (linkset)
 *   con service-desc apuntando a {siteUrl}/openapi.json (mismo origen,
 *   no al API Gateway).
 */
import { describe, expect, it } from 'vitest'

import { buildApiCatalog } from '../../src/lib/build-api-catalog'

describe('buildApiCatalog', () => {
  it('Given siteUrl When build Then JSON valido con linkset anchor + service-desc al mismo origen', () => {
    const out = buildApiCatalog({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    expect(parsed.linkset).toHaveLength(1)
    expect(parsed.linkset[0].anchor).toBe('https://the-full-stack.com')
    expect(parsed.linkset[0]['service-desc']).toHaveLength(1)
    expect(parsed.linkset[0]['service-desc'][0]).toEqual({
      href: 'https://the-full-stack.com/openapi.json',
      type: 'application/json',
    })
  })

  it('Given siteUrl con trailing slash When build Then strippa la slash', () => {
    const out = buildApiCatalog({ siteUrl: 'https://x.com/' })

    const parsed = JSON.parse(out)
    expect(parsed.linkset[0].anchor).toBe('https://x.com')
    expect(parsed.linkset[0]['service-desc'][0].href).toBe(
      'https://x.com/openapi.json',
    )
  })

  it('Given se invoca con apiEndpoint legacy When build Then se ignora (mantiene compat de firma)', () => {
    const out = buildApiCatalog({
      siteUrl: 'https://the-full-stack.com',
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })

    const parsed = JSON.parse(out)
    // El openapi.json ahora vive en el portfolio, NO en el API Gateway
    expect(parsed.linkset[0]['service-desc'][0].href).toBe(
      'https://the-full-stack.com/openapi.json',
    )
  })

  it('Given se invoca When inspecciono Then termina con newline', () => {
    const out = buildApiCatalog({ siteUrl: 'https://x.com' })

    expect(out.endsWith('\n')).toBe(true)
  })

  it('Given se invoca When inspecciono Then es JSON pretty-printed (indent 2)', () => {
    const out = buildApiCatalog({ siteUrl: 'https://x.com' })

    expect(out).toContain('  "linkset"')
    expect(out).toContain('    {')
  })
})
