/**
 * @description Tests para buildProfilePageSchema. Cubre AC-7 (JSON-LD
 *   ProfilePage enriquecido para GEO).
 */

import { profile } from '@portfolio/content'
import { describe, expect, it } from 'vitest'
import { buildProfilePageSchema } from '../../src/lib/build-profile-page-schema'

describe('buildProfilePageSchema', () => {
  it('Given fintech niche en When build Then top-level is ProfilePage con mainEntity Person', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'fintech',
      locale: 'en',
      canonicalUrl: 'https://fintech.the-full-stack.com/',
      knowsAbout: ['Vue', 'Django'],
    })
    const parsed = JSON.parse(ld)
    expect(parsed['@context']).toBe('https://schema.org')
    expect(parsed['@type']).toBe('ProfilePage')
    expect(parsed.mainEntity['@type']).toBe('Person')
    expect(parsed.mainEntity.name).toBe('Pablo Contreras')
    expect(parsed.mainEntity.email).toBe('pacg1991@gmail.com')
  })

  it('Given fintech niche en When build Then jobTitle matches LATAM Fintech', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'fintech',
      locale: 'en',
      canonicalUrl: 'https://fintech.the-full-stack.com/',
      knowsAbout: ['Vue', 'Django'],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.jobTitle).toBe(
      'Senior Full Stack Engineer — LATAM Fintech',
    )
  })

  it('Given architect niche es When build Then jobTitle es en espanol', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'architect',
      locale: 'es',
      canonicalUrl: 'https://architect.the-full-stack.com/',
      knowsAbout: [],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.jobTitle).toBe(
      'Arquitecto de Software y Microservicios',
    )
  })

  it('Given vibe niche en When build Then jobTitle menciona Claude Code', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'vibe',
      locale: 'en',
      canonicalUrl: 'https://vibe.the-full-stack.com/',
      knowsAbout: [],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.jobTitle).toBe(
      'AI-Augmented Software Engineer (Claude Code, Cursor)',
    )
  })

  it('Given build Then hasOccupation con skills concatenadas con coma-espacio', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'generic',
      locale: 'en',
      canonicalUrl: 'https://x.example/',
      knowsAbout: ['Vue', 'Django', 'AWS'],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.hasOccupation['@type']).toBe('Occupation')
    expect(parsed.mainEntity.hasOccupation.skills).toBe('Vue, Django, AWS')
  })

  it('Given locale es When build Then occupationLocation country es "Perú"', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'generic',
      locale: 'es',
      canonicalUrl: 'https://x.example/',
      knowsAbout: [],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.hasOccupation.occupationLocation.name).toBe('Perú')
  })

  it('Given locale en When build Then occupationLocation country es "Peru"', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'generic',
      locale: 'en',
      canonicalUrl: 'https://x.example/',
      knowsAbout: [],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.hasOccupation.occupationLocation.name).toBe('Peru')
  })

  it('Given build Then sameAs contiene linkedin, github y medium', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'generic',
      locale: 'en',
      canonicalUrl: 'https://x.example/',
      knowsAbout: [],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.sameAs).toContain(
      'https://linkedin.com/in/bypabloc',
    )
    expect(parsed.mainEntity.sameAs).toContain('https://github.com/bypabloc')
    expect(parsed.mainEntity.sameAs).toContain('https://bypablo.medium.com')
  })

  it('Given build Then dateModified es ISO date YYYY-MM-DD', () => {
    const ld = buildProfilePageSchema({
      profile,
      niche: 'generic',
      locale: 'en',
      canonicalUrl: 'https://x.example/',
      knowsAbout: [],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.dateModified).toMatch(/^\d{4}-\d{2}-\d{2}$/u)
  })

  it('Given profile sin medium ni website When build Then sameAs solo tiene linkedin+github', () => {
    const profileMinimal = {
      ...profile,
      contacts: {
        email: profile.contacts.email,
        linkedin: profile.contacts.linkedin,
        github: profile.contacts.github,
      },
    }
    const ld = buildProfilePageSchema({
      profile: profileMinimal,
      niche: 'generic',
      locale: 'en',
      canonicalUrl: 'https://x.example/',
      knowsAbout: [],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.mainEntity.sameAs).toHaveLength(2)
  })
})
