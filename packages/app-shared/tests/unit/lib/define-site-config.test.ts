/**
 * @description Tests para defineSiteConfig. Cubre el comportamiento de
 *   defaults (SITE_URL derivado del niche, OG_IMAGE sobre SITE_URL) y que
 *   STRINGS se compone desde los YAML i18n de @portfolio/content.
 */
import { describe, expect, it } from 'vitest'
import { defineSiteConfig } from '../../../src/lib/define-site-config'

describe('defineSiteConfig', () => {
  it('Given niche fintech without siteUrl When invoked Then SITE_URL derives from niche', () => {
    const r = defineSiteConfig({ niche: 'fintech' })
    expect(r.SITE_URL).toBe('https://fintech.portfolio.the-full-stack.com')
  })

  it('Given niche architect Then SITE_URL uses architect subdomain', () => {
    const r = defineSiteConfig({ niche: 'architect' })
    expect(r.SITE_URL).toBe('https://architect.portfolio.the-full-stack.com')
  })

  it('Given niche generic Then SITE_URL is the apex domain (env-driven default)', () => {
    const r = defineSiteConfig({ niche: 'generic' })
    expect(r.SITE_URL).toBe('https://the-full-stack.com')
  })

  it('Given explicit siteUrl When invoked Then SITE_URL is the provided value', () => {
    const r = defineSiteConfig({
      niche: 'leader',
      siteUrl: 'https://example.test',
    })
    expect(r.SITE_URL).toBe('https://example.test')
  })

  it('Given default ogImagePath When invoked Then OG_IMAGE is SITE_URL + /og-image.svg', () => {
    const r = defineSiteConfig({ niche: 'vibe' })
    expect(r.OG_IMAGE).toBe(
      'https://vibe.portfolio.the-full-stack.com/og-image.svg',
    )
  })

  it('Given custom ogImagePath When invoked Then OG_IMAGE uses the custom path', () => {
    const r = defineSiteConfig({
      niche: 'fintech',
      ogImagePath: '/custom-og.png',
    })
    expect(r.OG_IMAGE).toBe(
      'https://fintech.portfolio.the-full-stack.com/custom-og.png',
    )
  })

  it('Given valid input When invoked Then NICHE === niche', () => {
    const r = defineSiteConfig({ niche: 'leader' })
    expect(r.NICHE).toBe('leader')
  })

  it('Given niche fintech When invoked Then STRINGS.es.meta.title is the fintech curriculum title', () => {
    const r = defineSiteConfig({ niche: 'fintech' })
    expect(r.STRINGS.es.meta.title).toBe(
      'Pablo Contreras — Senior Full Stack Fintech LATAM',
    )
  })

  it('Given niche vibe When invoked Then STRINGS.en.hero.headline is the vibe curriculum headline', () => {
    const r = defineSiteConfig({ niche: 'vibe' })
    expect(r.STRINGS.en.hero.headline).toBe(
      'AI-Augmented Full Stack · Claude Code',
    )
  })

  it('Given a niche app When invoked Then the nav includes the hub item', () => {
    const r = defineSiteConfig({ niche: 'fintech' })
    const labels = r.STRINGS.es.nav.map((n) => n.label)
    expect(labels).toEqual([
      'Experiencia',
      'Proyectos',
      'Skills',
      'Sobre mí',
      'Certificados',
      'Contacto',
      'Otras vistas',
    ])
  })

  it('Given app hub with omitNicheDropdown true When invoked Then the nav omits the hub item', () => {
    const r = defineSiteConfig({
      niche: 'generic',
      app: 'hub',
      omitNicheDropdown: true,
    })
    const labels = r.STRINGS.es.nav.map((n) => n.label)
    expect(labels).toEqual([
      'Experiencia',
      'Proyectos',
      'Skills',
      'Sobre mí',
      'Certificados',
      'Contacto',
    ])
  })

  it('Given a niche app When invoked Then the hub nav item is a dropdown with 5 niches', () => {
    const r = defineSiteConfig({ niche: 'fintech' })
    const hubItem = r.STRINGS.es.nav.find((n) => n.label === 'Otras vistas')
    expect(hubItem?.dropdownItems?.length).toBe(5)
    expect(
      hubItem?.dropdownItems?.find((d) => d.niche === 'fintech')?.current,
    ).toBe(true)
    expect(
      hubItem?.dropdownItems?.find((d) => d.niche === 'architect')?.current,
    ).toBe(false)
  })
})
