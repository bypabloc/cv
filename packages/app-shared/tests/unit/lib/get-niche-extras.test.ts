/**
 * @description Tests para getNicheExtras: mapeo niche -> secciones extras.
 */
import { describe, expect, it } from 'vitest'
import { getNicheExtras } from '../../../src/lib/get-niche-extras'

describe('getNicheExtras', () => {
  it('Given niche generic When getNicheExtras Then retorna StatsBar y SkillsMarquee', () => {
    const result = getNicheExtras('generic')
    expect(result).toStrictEqual(['StatsBar', 'SkillsMarquee'])
  })

  it('Given niche fintech When getNicheExtras Then incluye AtsKeywordsPills', () => {
    const result = getNicheExtras('fintech')
    expect(result).toStrictEqual([
      'StatsBar',
      'AtsKeywordsPills',
      'SkillsMarquee',
    ])
  })

  it('Given niche architect When getNicheExtras Then incluye ArchitectureDiagram', () => {
    const result = getNicheExtras('architect')
    expect(result).toStrictEqual([
      'StatsBar',
      'ArchitectureDiagram',
      'SkillsMarquee',
    ])
  })

  it('Given niche leader When getNicheExtras Then incluye LeadershipStats y AwardsHighlight', () => {
    const result = getNicheExtras('leader')
    expect(result).toStrictEqual([
      'StatsBar',
      'LeadershipStats',
      'AwardsHighlight',
      'SkillsMarquee',
    ])
  })

  it('Given niche vibe When getNicheExtras Then incluye AiWorkflowSection', () => {
    const result = getNicheExtras('vibe')
    expect(result).toStrictEqual([
      'StatsBar',
      'AiWorkflowSection',
      'SkillsMarquee',
    ])
  })

  it('Given todos los niches When getNicheExtras Then todos contienen StatsBar primero', () => {
    const niches = [
      'generic',
      'fintech',
      'architect',
      'leader',
      'vibe',
    ] as const
    for (const n of niches) {
      const result = getNicheExtras(n)
      expect(result[0]).toBe('StatsBar')
    }
  })

  it('Given todos los niches When getNicheExtras Then todos terminan con SkillsMarquee', () => {
    const niches = [
      'generic',
      'fintech',
      'architect',
      'leader',
      'vibe',
    ] as const
    for (const n of niches) {
      const result = getNicheExtras(n)
      expect(result[result.length - 1]).toBe('SkillsMarquee')
    }
  })
})
