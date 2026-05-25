/**
 * @description Tests para buildWebSiteSchema. JSON-LD WebSite que
 *   complementa al ProfilePage existente del home.
 */
import { describe, expect, it } from 'vitest'

import { buildWebSiteSchema } from '../../src/lib/build-website-schema'

describe('buildWebSiteSchema', () => {
  it('Given siteUrl + name When build Then JSON string con @context + @type WebSite', () => {
    const json = buildWebSiteSchema({
      siteUrl: 'https://the-full-stack.com',
      name: 'Pablo Contreras — Portfolio',
    })
    const out = JSON.parse(json)

    expect(out['@context']).toBe('https://schema.org')
    expect(out['@type']).toBe('WebSite')
    expect(out.name).toBe('Pablo Contreras — Portfolio')
    expect(out.url).toBe('https://the-full-stack.com')
  })

  it('Given sin inLanguage When build Then default [es, en]', () => {
    const out = JSON.parse(
      buildWebSiteSchema({
        siteUrl: 'https://x.com',
        name: 'X',
      }),
    )

    expect(out.inLanguage).toEqual(['es', 'en'])
  })

  it('Given inLanguage explicito When build Then usa los proporcionados', () => {
    const out = JSON.parse(
      buildWebSiteSchema({
        siteUrl: 'https://x.com',
        name: 'X',
        inLanguage: ['en'],
      }),
    )

    expect(out.inLanguage).toEqual(['en'])
  })

  it('Given se invoca When inspecciono Then returna string parseable', () => {
    const out = buildWebSiteSchema({
      siteUrl: 'https://x.com',
      name: 'X',
    })

    expect(typeof out).toBe('string')
    expect(out).toContain('"@type":"WebSite"')
  })
})
