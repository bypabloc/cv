/**
 * @description Tests para buildApiCatalog. Genera JSON RFC9727 (linkset)
 *   para /.well-known/api-catalog.
 */
import { describe, expect, it } from 'vitest'

import { buildApiCatalog } from '../../src/lib/build-api-catalog'

describe('buildApiCatalog', () => {
  it('Given siteUrl + apiEndpoint When build Then JSON valido con shape linkset', () => {
    const out = buildApiCatalog({
      siteUrl: 'https://the-full-stack.com',
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })

    const parsed = JSON.parse(out)
    expect(parsed.linkset).toHaveLength(1)
    expect(parsed.linkset[0].anchor).toBe('https://the-full-stack.com')
    expect(parsed.linkset[0]['service-desc']).toHaveLength(1)
    expect(parsed.linkset[0]['service-desc'][0]).toEqual({
      href: 'https://api.portfolio.the-full-stack.com/openapi.json',
      type: 'application/json',
    })
  })

  it('Given apiEndpoint con trailing slash When build Then strippa la slash antes de /openapi.json', () => {
    const out = buildApiCatalog({
      siteUrl: 'https://x.com',
      apiEndpoint: 'https://api.x.com/',
    })

    const parsed = JSON.parse(out)
    expect(parsed.linkset[0]['service-desc'][0].href).toBe(
      'https://api.x.com/openapi.json',
    )
  })

  it('Given se invoca When inspecciono Then termina con newline', () => {
    const out = buildApiCatalog({
      siteUrl: 'https://x.com',
      apiEndpoint: 'https://api.x.com',
    })

    expect(out.endsWith('\n')).toBe(true)
  })

  it('Given se invoca When inspecciono Then es JSON pretty-printed (indent 2)', () => {
    const out = buildApiCatalog({
      siteUrl: 'https://x.com',
      apiEndpoint: 'https://api.x.com',
    })

    expect(out).toContain('  "linkset"')
    expect(out).toContain('    {')
  })
})
