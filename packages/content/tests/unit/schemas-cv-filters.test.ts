/**
 * @description Tests para los campos nuevos del schema agregados por el feature
 *   CV filters via query params (docs/specs/cv-filters-query-params.md):
 *
 *   - ExperienceSchema.seniority: 'intern' | 'junior' | 'mid' | 'senior' | 'lead'
 *   - ProjectSchema.projectType: 'web' | 'mobile' | 'cli' | 'library' | 'ai' | 'fintech-platform'
 *
 *   Cubre AC-1, AC-2, AC-3.
 */
import { describe, expect, it } from 'vitest'
import { experiences, projects } from '../../src/index'
import {
  ExperienceSchema,
  type Niche,
  PROJECT_TYPES,
  ProjectSchema,
  SENIORITIES,
} from '../../src/schemas'

const allNiches: Niche[] = ['fintech', 'architect', 'leader', 'vibe', 'generic']

function buildValidExperienceBase() {
  return {
    slug: 'test',
    role: { es: 'Rol', en: 'Role' },
    company: 'Acme',
    country: 'Perú',
    start: '2024-01',
    niches: ['generic'] as Niche[],
    responsibilities: { es: ['a'], en: ['a'] },
    achievements: { es: [], en: [] },
    skillsTechnical: [],
    skillsSoft: [],
  }
}

function buildValidProjectBase() {
  return {
    slug: 'test',
    name: 'Test',
    summary: { es: 'a', en: 'a' },
    status: 'active' as const,
    niches: ['generic'] as Niche[],
    stack: ['TypeScript'],
  }
}

describe('ExperienceSchema.seniority [AC-1]', () => {
  it('Given an experience without seniority When parsing Then schema fails', () => {
    expect(() => ExperienceSchema.parse(buildValidExperienceBase())).toThrow()
  })

  it.each(
    SENIORITIES,
  )('Given seniority "%s" When parsing Then schema accepts it', (value) => {
    const parsed = ExperienceSchema.parse({
      ...buildValidExperienceBase(),
      seniority: value,
    })
    expect(parsed.seniority).toBe(value)
  })

  it('Given seniority "invalid" When parsing Then schema fails', () => {
    expect(() =>
      ExperienceSchema.parse({
        ...buildValidExperienceBase(),
        seniority: 'invalid',
      }),
    ).toThrow()
  })
})

describe('ExperienceSchema.country', () => {
  it('Given an experience with country When parsing Then schema accepts it', () => {
    const parsed = ExperienceSchema.parse({
      ...buildValidExperienceBase(),
      seniority: 'senior',
    })
    expect(parsed.country).toBe('Perú')
  })

  it('Given an experience without country When parsing Then schema fails', () => {
    const { country: _omit, ...withoutCountry } = buildValidExperienceBase()
    expect(() =>
      ExperienceSchema.parse({ ...withoutCountry, seniority: 'senior' }),
    ).toThrow()
  })
})

describe('ExperienceSchema.metricsEstimated', () => {
  it('Given an experience without metricsEstimated When parsing Then defaults to false', () => {
    const parsed = ExperienceSchema.parse({
      ...buildValidExperienceBase(),
      seniority: 'senior',
    })
    expect(parsed.metricsEstimated).toBe(false)
  })

  it('Given an experience with metricsEstimated true When parsing Then keeps it', () => {
    const parsed = ExperienceSchema.parse({
      ...buildValidExperienceBase(),
      seniority: 'senior',
      metricsEstimated: true,
    })
    expect(parsed.metricsEstimated).toBe(true)
  })
})

describe('ProjectSchema.metricsEstimated', () => {
  it('Given a project without metricsEstimated When parsing Then defaults to false', () => {
    const parsed = ProjectSchema.parse({
      ...buildValidProjectBase(),
      projectType: 'web',
    })
    expect(parsed.metricsEstimated).toBe(false)
  })

  it('Given a project with metricsEstimated true When parsing Then keeps it', () => {
    const parsed = ProjectSchema.parse({
      ...buildValidProjectBase(),
      projectType: 'web',
      metricsEstimated: true,
    })
    expect(parsed.metricsEstimated).toBe(true)
  })
})

describe('ProjectSchema.projectType [AC-2]', () => {
  it('Given a project without projectType When parsing Then schema fails', () => {
    expect(() => ProjectSchema.parse(buildValidProjectBase())).toThrow()
  })

  it.each(
    PROJECT_TYPES,
  )('Given projectType "%s" When parsing Then schema accepts it', (value) => {
    const parsed = ProjectSchema.parse({
      ...buildValidProjectBase(),
      projectType: value,
    })
    expect(parsed.projectType).toBe(value)
  })

  it('Given projectType "invalid" When parsing Then schema fails', () => {
    expect(() =>
      ProjectSchema.parse({
        ...buildValidProjectBase(),
        projectType: 'invalid',
      }),
    ).toThrow()
  })
})

describe('backfill completeness [AC-3]', () => {
  it('Given all loaded experiences Then every entry has a valid seniority', () => {
    const validSeniorities = new Set(SENIORITIES)
    for (const exp of experiences) {
      expect(validSeniorities.has(exp.seniority)).toBe(true)
    }
  })

  it('Given all loaded projects Then every entry has a valid projectType', () => {
    const validTypes = new Set(PROJECT_TYPES)
    for (const proj of projects) {
      expect(validTypes.has(proj.projectType)).toBe(true)
    }
  })

  it('Given current experiences fixture Then expected slug -> seniority mapping matches', () => {
    const map = new Map(experiences.map((e) => [e.slug, e.seniority]))
    expect(map.get('cofasa')).toBe('mid')
    expect(map.get('corpoelec')).toBe('intern')
    expect(map.get('destacame-architect')).toBe('lead')
    expect(map.get('destacame-frontend')).toBe('senior')
    expect(map.get('dibal')).toBe('senior')
    expect(map.get('goodmeal')).toBe('mid')
    expect(map.get('iai')).toBe('mid')
    expect(map.get('ipasme')).toBe('junior')
    expect(map.get('projects-degrees')).toBe('mid')
  })

  it('Given current projects fixture Then expected slug -> projectType mapping matches', () => {
    const map = new Map(projects.map((p) => [p.slug, p.projectType]))
    expect(map.get('destacame-credit-mexico')).toBe('fintech-platform')
    expect(map.get('destacame-debt-chile')).toBe('fintech-platform')
    expect(map.get('faststruct')).toBe('cli')
    expect(map.get('mvp-template-full-stack')).toBe('library')
    expect(projects.length).toBe(4)
  })
})

describe('SENIORITIES + PROJECT_TYPES exports', () => {
  it('Given the exported SENIORITIES Then it lists 5 ordered levels', () => {
    expect(SENIORITIES).toEqual(['intern', 'junior', 'mid', 'senior', 'lead'])
  })

  it('Given the exported PROJECT_TYPES Then it lists 6 categories', () => {
    expect(PROJECT_TYPES).toEqual([
      'web',
      'mobile',
      'cli',
      'library',
      'ai',
      'fintech-platform',
    ])
  })

  it('Given allNiches reference Then it contains exactly 5 niches', () => {
    expect(allNiches).toHaveLength(5)
  })
})
