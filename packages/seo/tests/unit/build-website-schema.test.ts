/**
 * @description Tests para buildWebSiteSchema. JSON-LD WebSite que
 *   complementa al ProfilePage existente del home.
 */
import { describe, expect, it } from 'vitest'

import { buildWebSiteSchema } from '../../src/lib/build-website-schema'

describe('buildWebSiteSchema', () => {
  it('Given siteUrl + name When build Then schema con @context + @type WebSite', () => {
    const out = buildWebSiteSchema({
      siteUrl: 'https://the-full-stack.com',
      name: 'Pablo Contreras — Portfolio',
    })

    expect(out['@context']).toBe('https://schema.org')
    expect(out['@type']).toBe('WebSite')
    expect(out.name).toBe('Pablo Contreras — Portfolio')
    expect(out.url).toBe('https://the-full-stack.com')
  })

  it('Given sin inLanguage When build Then default [es, en]', () => {
    const out = buildWebSiteSchema({
      siteUrl: 'https://x.com',
      name: 'X',
    })

    expect(out.inLanguage).toEqual(['es', 'en'])
  })

  it('Given inLanguage explicito When build Then usa los proporcionados', () => {
    const out = buildWebSiteSchema({
      siteUrl: 'https://x.com',
      name: 'X',
      inLanguage: ['en'],
    })

    expect(out.inLanguage).toEqual(['en'])
  })

  it('Given se invoca When JSON.stringify Then serializa sin error', () => {
    const out = buildWebSiteSchema({
      siteUrl: 'https://x.com',
      name: 'X',
    })

    const serialized = JSON.stringify(out)
    expect(serialized).toContain('"@type":"WebSite"')
  })
})
