/**
 * @description Tests para niche-tokens: mapeo type-safe niche -> tokens
 *   visuales (accent, glow, gradient, mood).
 */
import { describe, expect, it } from 'vitest'
import {
  getNicheTokens,
  NICHE_TOKENS,
  nicheTokensToCssVars,
} from '../../src/lib/niche-tokens'

describe('NICHE_TOKENS', () => {
  it('Given NICHE_TOKENS Then contiene los 5 niches + hub (6 entries)', () => {
    expect(Object.keys(NICHE_TOKENS).sort()).toStrictEqual([
      'architect',
      'fintech',
      'generic',
      'hub',
      'leader',
      'vibe',
    ])
  })
})

describe('getNicheTokens', () => {
  it('Given niche fintech Then accent es cyan #38d9d6', () => {
    expect(getNicheTokens('fintech').accent).toBe('#38d9d6')
  })

  it('Given niche architect Then accent es rose #f06e9c y mood es mono', () => {
    const t = getNicheTokens('architect')
    expect(t.accent).toBe('#f06e9c')
    expect(t.mood).toBe('mono')
  })

  it('Given niche leader Then accent es amber #f4b740', () => {
    expect(getNicheTokens('leader').accent).toBe('#f4b740')
  })

  it('Given niche vibe Then accent es purple #b97cf2 y mood es mono', () => {
    const t = getNicheTokens('vibe')
    expect(t.accent).toBe('#b97cf2')
    expect(t.mood).toBe('mono')
  })

  it('Given niche generic Then accent es electric blue #4f6ef7 y mood es sans', () => {
    const t = getNicheTokens('generic')
    expect(t.accent).toBe('#4f6ef7')
    expect(t.mood).toBe('sans')
  })

  it('Given niche hub Then label es "Hub"', () => {
    expect(getNicheTokens('hub').label).toBe('Hub')
  })

  it('Given todos los niches Then accentRgb es triplet "r, g, b"', () => {
    const niches = [
      'generic',
      'hub',
      'fintech',
      'architect',
      'leader',
      'vibe',
    ] as const
    for (const n of niches) {
      const t = getNicheTokens(n)
      expect(t.accentRgb).toMatch(/^\d+, \d+, \d+$/u)
    }
  })
})

describe('nicheTokensToCssVars', () => {
  it('Given niche fintech Then string contiene 5 custom props separadas por "; "', () => {
    const css = nicheTokensToCssVars('fintech')
    expect(css).toBe(
      '--niche-accent: #38d9d6; --niche-accent-rgb: 56, 217, 214; --niche-glow: rgba(56, 217, 214, 0.35); --niche-gradient: linear-gradient(135deg, #38d9d6 0%, #4f6ef7 100%); --niche-mood: sans',
    )
  })

  it('Given niche vibe Then incluye mood: mono', () => {
    const css = nicheTokensToCssVars('vibe')
    expect(css).toContain('--niche-mood: mono')
  })
})
