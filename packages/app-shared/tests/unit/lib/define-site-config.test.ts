/**
 * @description Tests para defineSiteConfig. Cubre AC-9 (helper reduce
 *   boilerplate de site-config.ts por app) + comportamiento de defaults
 *   (SITE_URL derivado del niche, OG_IMAGE construido sobre SITE_URL).
 */
import { describe, expect, it } from 'vitest'
import { defineSiteConfig } from '../../../src/lib/define-site-config'

const baseOverrides = {
  metaTitleEs: 'titulo es',
  metaTitleEn: 'title en',
  metaDescriptionEs: 'desc es',
  metaDescriptionEn: 'desc en',
}

describe('defineSiteConfig', () => {
  it('Given niche fintech without siteUrl When invoked Then SITE_URL derives from niche', () => {
    const r = defineSiteConfig({ niche: 'fintech', overrides: baseOverrides })
    expect(r.SITE_URL).toBe('https://fintech.portfolio.the-full-stack.com')
  })

  it('Given niche architect Then SITE_URL uses architect subdomain', () => {
    const r = defineSiteConfig({ niche: 'architect', overrides: baseOverrides })
    expect(r.SITE_URL).toBe('https://architect.portfolio.the-full-stack.com')
  })

  it('Given niche generic Then SITE_URL is the apex domain (env-driven default)', () => {
    const r = defineSiteConfig({ niche: 'generic', overrides: baseOverrides })
    expect(r.SITE_URL).toBe('https://the-full-stack.com')
  })

  it('Given explicit siteUrl When invoked Then SITE_URL is the provided value', () => {
    const r = defineSiteConfig({
      niche: 'leader',
      siteUrl: 'https://example.test',
      overrides: baseOverrides,
    })
    expect(r.SITE_URL).toBe('https://example.test')
  })

  it('Given default ogImagePath When invoked Then OG_IMAGE is SITE_URL + /og-image.svg', () => {
    const r = defineSiteConfig({ niche: 'vibe', overrides: baseOverrides })
    expect(r.OG_IMAGE).toBe(
      'https://vibe.portfolio.the-full-stack.com/og-image.svg',
    )
  })

  it('Given custom ogImagePath When invoked Then OG_IMAGE uses the custom path', () => {
    const r = defineSiteConfig({
      niche: 'fintech',
      ogImagePath: '/custom-og.png',
      overrides: baseOverrides,
    })
    expect(r.OG_IMAGE).toBe(
      'https://fintech.portfolio.the-full-stack.com/custom-og.png',
    )
  })

  it('Given valid input When invoked Then NICHE === niche', () => {
    const r = defineSiteConfig({ niche: 'leader', overrides: baseOverrides })
    expect(r.NICHE).toBe('leader')
  })

  it('Given overrides When invoked Then STRINGS.es.meta has the provided title', () => {
    const r = defineSiteConfig({
      niche: 'generic',
      overrides: { ...baseOverrides, metaTitleEs: 'mi titulo unico' },
    })
    expect(r.STRINGS.es.meta.title).toBe('mi titulo unico')
  })

  it('Given overrides When invoked Then STRINGS.en.meta has the provided title', () => {
    const r = defineSiteConfig({
      niche: 'generic',
      overrides: { ...baseOverrides, metaTitleEn: 'unique title' },
    })
    expect(r.STRINGS.en.meta.title).toBe('unique title')
  })
})
