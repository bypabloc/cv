/**
 * @description Tests para matchesFilter(). Cubre AC-4 (OR intra-dim), AC-5
 *   (AND inter-dim), AC-6 (rango fechas), AC-7 (skills), AC-8 (confidential).
 */
import { describe, expect, it } from 'vitest'
import { matchesFilter } from '../../src/matches-filter'
import { emptyFilterState, type ItemAttrs } from '../../src/types'

function buildAttrs(overrides: Partial<ItemAttrs> = {}): ItemAttrs {
  return {
    tech: [],
    seniority: '',
    projectType: '',
    skillKind: '',
    start: '',
    end: '',
    confidential: false,
    ...overrides,
  }
}

describe('matchesFilter [AC-4 OR intra-dim]', () => {
  it('Given empty state Then any item matches', () => {
    const item = buildAttrs({ tech: ['Vue'] })
    expect(matchesFilter(item, emptyFilterState())).toBe(true)
  })

  it('Given tech=[Vue,Django] and item has Vue Then matches', () => {
    const item = buildAttrs({ tech: ['Vue', 'Astro'] })
    expect(
      matchesFilter(item, { ...emptyFilterState(), tech: ['Vue', 'Django'] }),
    ).toBe(true)
  })

  it('Given tech=[Vue,Django] and item has only Python Then no match', () => {
    const item = buildAttrs({ tech: ['Python'] })
    expect(
      matchesFilter(item, { ...emptyFilterState(), tech: ['Vue', 'Django'] }),
    ).toBe(false)
  })

  it('Given tech=[Vue] and item has empty tech Then no match', () => {
    const item = buildAttrs({ tech: [] })
    expect(matchesFilter(item, { ...emptyFilterState(), tech: ['Vue'] })).toBe(
      false,
    )
  })

  it('Given seniority=[senior,lead] and item is mid Then no match', () => {
    const item = buildAttrs({ seniority: 'mid' })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        seniority: ['senior', 'lead'],
      }),
    ).toBe(false)
  })

  it('Given seniority=[senior,lead] and item is senior Then matches', () => {
    const item = buildAttrs({ seniority: 'senior' })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        seniority: ['senior', 'lead'],
      }),
    ).toBe(true)
  })

  it('Given seniority=[senior] and item has no seniority Then no match', () => {
    const item = buildAttrs({ seniority: '' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), seniority: ['senior'] }),
    ).toBe(false)
  })

  it('Given projectType=[web] and item is web Then matches', () => {
    const item = buildAttrs({ projectType: 'web' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), projectType: ['web'] }),
    ).toBe(true)
  })

  it('Given projectType=[web] and item is cli Then no match', () => {
    const item = buildAttrs({ projectType: 'cli' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), projectType: ['web'] }),
    ).toBe(false)
  })
})

describe('matchesFilter [AC-5 AND inter-dim]', () => {
  it('Given tech=[Vue] AND seniority=[senior], item has Vue+senior Then matches', () => {
    const item = buildAttrs({ tech: ['Vue'], seniority: 'senior' })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        tech: ['Vue'],
        seniority: ['senior'],
      }),
    ).toBe(true)
  })

  it('Given tech=[Vue] AND seniority=[senior], item has Vue+junior Then no match', () => {
    const item = buildAttrs({ tech: ['Vue'], seniority: 'junior' })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        tech: ['Vue'],
        seniority: ['senior'],
      }),
    ).toBe(false)
  })

  it('Given tech=[Vue] AND seniority=[senior], item has Python+senior Then no match', () => {
    const item = buildAttrs({ tech: ['Python'], seniority: 'senior' })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        tech: ['Vue'],
        seniority: ['senior'],
      }),
    ).toBe(false)
  })
})

describe('matchesFilter [AC-6 date range]', () => {
  it('Given from=2022-01 and item ends 2021-12 Then no match', () => {
    const item = buildAttrs({ start: '2020-01', end: '2021-12' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), from: '2022-01' }),
    ).toBe(false)
  })

  it('Given from=2022-01 and item ends 2024-06 Then matches', () => {
    const item = buildAttrs({ start: '2020-01', end: '2024-06' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), from: '2022-01' }),
    ).toBe(true)
  })

  it('Given to=2024-12 and item starts 2025-01 Then no match', () => {
    const item = buildAttrs({ start: '2025-01', end: '2026-05' })
    expect(matchesFilter(item, { ...emptyFilterState(), to: '2024-12' })).toBe(
      false,
    )
  })

  it('Given item with open end and filter from=2024-01 Then matches', () => {
    const item = buildAttrs({ start: '2022-08', end: '' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), from: '2024-01' }),
    ).toBe(true)
  })
})

describe('matchesFilter [AC-7 skills kind]', () => {
  it('Given skills=[technical] and item is technical Then matches', () => {
    const item = buildAttrs({ skillKind: 'technical' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), skills: ['technical'] }),
    ).toBe(true)
  })

  it('Given skills=[technical] and item is soft Then no match', () => {
    const item = buildAttrs({ skillKind: 'soft' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), skills: ['technical'] }),
    ).toBe(false)
  })

  it('Given skills=[technical,soft] and item is technical Then matches', () => {
    const item = buildAttrs({ skillKind: 'technical' })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        skills: ['technical', 'soft'],
      }),
    ).toBe(true)
  })

  it('Given skills=[technical] and item has no skillKind Then no match', () => {
    const item = buildAttrs({ skillKind: '' })
    expect(
      matchesFilter(item, { ...emptyFilterState(), skills: ['technical'] }),
    ).toBe(false)
  })
})

describe('matchesFilter [AC-8 hideConfidential]', () => {
  it('Given hideConfidential=true and item confidential=true Then no match', () => {
    const item = buildAttrs({ confidential: true })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        hideConfidential: true,
      }),
    ).toBe(false)
  })

  it('Given hideConfidential=true and item confidential=false Then matches', () => {
    const item = buildAttrs({ confidential: false })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        hideConfidential: true,
      }),
    ).toBe(true)
  })

  it('Given hideConfidential=false (default) and item confidential=true Then matches', () => {
    const item = buildAttrs({ confidential: true })
    expect(
      matchesFilter(item, {
        ...emptyFilterState(),
        hideConfidential: false,
      }),
    ).toBe(true)
  })
})
