/**
 * @description Tests para buildPersonSchema. Cubre AC-2.
 */

import { profile } from '@portfolio/content'
import { describe, expect, it } from 'vitest'
import { buildPersonSchema } from '../../src/lib/build-person-schema'

describe('buildPersonSchema', () => {
  it('Given fintech niche en When build Then returns valid JSON-LD with fintech jobTitle', () => {
    const ld = buildPersonSchema({
      profile,
      niche: 'fintech',
      locale: 'en',
      canonicalUrl: 'https://fintech.the-full-stack.com/',
      knowsAbout: ['Vue', 'Django', 'AWS', 'Fintech'],
    })
    const parsed = JSON.parse(ld)
    expect(parsed['@context']).toBe('https://schema.org')
    expect(parsed['@type']).toBe('Person')
    expect(parsed.name).toBe('Pablo Contreras')
    expect(parsed.alternateName).toBe('bypabloc')
    expect(parsed.jobTitle).toMatch(/Fintech/u)
    expect(parsed.email).toBe('pacg1991@gmail.com')
    expect(parsed.url).toBe('https://fintech.the-full-stack.com/')
    expect(parsed.knowsAbout).toEqual(['Vue', 'Django', 'AWS', 'Fintech'])
    expect(parsed.address.addressLocality).toBe('Lima, Perú')
    expect(parsed.sameAs).toContain('https://linkedin.com/in/bypabloc')
    expect(parsed.sameAs).toContain('https://github.com/bypabloc')
  })

  it('Given architect niche es When build Then returns Spanish job title', () => {
    const ld = buildPersonSchema({
      profile,
      niche: 'architect',
      locale: 'es',
      canonicalUrl: 'https://architect.the-full-stack.com/',
      knowsAbout: ['Microservicios'],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.jobTitle).toMatch(/Arquitecto/u)
    expect(parsed.description).toMatch(/Ingeniero/u)
  })

  it('Given each niche When build Then jobTitle differs per niche', () => {
    const titles = (
      ['fintech', 'architect', 'leader', 'vibe', 'generic'] as const
    ).map(
      (n) =>
        JSON.parse(
          buildPersonSchema({
            profile,
            niche: n,
            locale: 'en',
            canonicalUrl: 'https://x.example/',
            knowsAbout: [],
          }),
        ).jobTitle as string,
    )
    expect(new Set(titles).size).toBe(5)
  })
})
