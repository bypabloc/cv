/**
 * @description Tests para buildLlmsTxt. Cubre AC-3.
 */

import { profile } from '@portfolio/content'
import { describe, expect, it } from 'vitest'
import { buildLlmsTxt } from '../../src/lib/build-llms-txt'

describe('buildLlmsTxt', () => {
  it('Given fintech niche When build Then contains H1, summary and pages', () => {
    const out = buildLlmsTxt({
      siteUrl: 'https://fintech.the-full-stack.com/',
      profile,
      niche: 'fintech',
      pages: [
        {
          path: '/',
          title: 'Home',
          description: 'Senior fintech engineer for LATAM',
        },
        {
          path: '/experience',
          title: 'Experience',
          description: '9 roles in 8 employers',
        },
      ],
    })
    expect(out).toMatch(/^# Pablo Contreras — fintech$/m)
    expect(out).toMatch(/Latin American fintech/u)
    expect(out).toMatch(/## Pages/u)
    expect(out).toContain(
      '- [Home](https://fintech.the-full-stack.com/): Senior fintech engineer for LATAM',
    )
    expect(out).toContain(
      '- [Experience](https://fintech.the-full-stack.com/experience): 9 roles in 8 employers',
    )
    expect(out).toContain('LinkedIn: https://linkedin.com/in/bypabloc')
    expect(out).toContain('GitHub: https://github.com/bypabloc')
  })

  it('Given page with absolute URL When build Then keeps URL as-is', () => {
    const out = buildLlmsTxt({
      siteUrl: 'https://x.example/',
      profile,
      niche: 'generic',
      pages: [
        {
          path: 'https://medium.com/@bypablo/foo',
          title: 'External',
          description: 'External post',
        },
      ],
    })
    expect(out).toContain(
      '- [External](https://medium.com/@bypablo/foo): External post',
    )
  })

  it('Given no medium contact When build Then omits medium line', () => {
    const trimmed = { ...profile, contacts: { ...profile.contacts } }
    trimmed.contacts.medium = undefined as unknown as string
    const out = buildLlmsTxt({
      siteUrl: 'https://x.example/',
      profile: trimmed,
      niche: 'generic',
      pages: [],
    })
    expect(out).not.toMatch(/Medium:/u)
  })

  it('Given profile con availability When build Then incluye Availability en metadata header', () => {
    const out = buildLlmsTxt({
      siteUrl: 'https://x.example/',
      profile,
      niche: 'generic',
      pages: [],
    })
    expect(out).toContain('Availability: Remote-friendly · LATAM/US timezone.')
  })

  it('Given profile sin availability When build Then omite Availability', () => {
    const stripped = { ...profile, availability: undefined }
    const out = buildLlmsTxt({
      siteUrl: 'https://x.example/',
      profile: stripped,
      niche: 'generic',
      pages: [],
    })
    expect(out).not.toMatch(/Availability:/u)
  })
})
