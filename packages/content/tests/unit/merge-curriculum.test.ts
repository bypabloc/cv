/**
 * @description Tests para mergeCurriculum. Cubre AC-5: una clave ausente en
 *   el override de la app cae al valor del `_base`.
 */
import { describe, expect, it } from 'vitest'
import { mergeCurriculum } from '../../src/lib/merge-curriculum'
import type { CurriculumOverride, CurriculumStrings } from '../../src/schemas'

const base: CurriculumStrings = {
  meta: { title: 'base title', description: 'base description' },
  hero: {
    eyebrow: 'base eyebrow',
    headline: 'base headline',
    summary: 'base summary',
    nicheLabel: 'base label',
  },
  sections: {
    experienceSubtitle: 'base exp',
    projectsSubtitle: 'base proj',
    skillsSubtitle: 'base skills',
    contactSubtitle: 'base contact',
    certificatesSubtitle: 'base certs',
    awardsSubtitle: 'base awards',
  },
  atsKeywords: ['base-kw'],
}

describe('mergeCurriculum', () => {
  it('Given an empty override When merged Then result equals the base', () => {
    const result = mergeCurriculum(base, {})
    expect(result).toEqual(base)
  })

  it('Given a hero headline override When merged Then headline is overridden but summary stays base', () => {
    const override: CurriculumOverride = {
      hero: { headline: 'app headline' },
    }
    const result = mergeCurriculum(base, override)
    expect(result.hero.headline).toBe('app headline')
    expect(result.hero.summary).toBe('base summary')
  })

  it('Given a hero summary override When merged Then the niche summary wins over the base', () => {
    const override: CurriculumOverride = {
      hero: { summary: 'niche summary' },
    }
    const result = mergeCurriculum(base, override)
    expect(result.hero.summary).toBe('niche summary')
  })

  it('Given a partial sections override When merged Then absent subtitles fall back to base', () => {
    const override: CurriculumOverride = {
      sections: { experienceSubtitle: 'app exp' },
    }
    const result = mergeCurriculum(base, override)
    expect(result.sections.experienceSubtitle).toBe('app exp')
    expect(result.sections.skillsSubtitle).toBe('base skills')
  })

  it('Given an atsKeywords override When merged Then the array is fully replaced', () => {
    const override: CurriculumOverride = {
      atsKeywords: ['app-kw-1', 'app-kw-2'],
    }
    const result = mergeCurriculum(base, override)
    expect(result.atsKeywords).toEqual(['app-kw-1', 'app-kw-2'])
  })

  it('Given a meta override When merged Then meta is overridden field by field', () => {
    const override: CurriculumOverride = {
      meta: { title: 'app title' },
    }
    const result = mergeCurriculum(base, override)
    expect(result.meta.title).toBe('app title')
    expect(result.meta.description).toBe('base description')
  })
})
