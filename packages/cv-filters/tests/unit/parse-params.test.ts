/**
 * @description Tests para parseParams() y serializeState(). Cubre AC-4 (parsing
 *   correcto de listas CSV), AC-10 (params invalidos ignorados), AC-13 (clear).
 */
import { describe, expect, it } from 'vitest'
import { parseParams, serializeState } from '../../src/parse-params'
import { emptyFilterState } from '../../src/types'

describe('parseParams [AC-4, AC-10]', () => {
  it('Given empty URLSearchParams Then returns empty state', () => {
    const state = parseParams(new URLSearchParams(''))
    expect(state).toEqual(emptyFilterState())
  })

  it('Given ?tech=Vue,Django Then returns { tech: ["Vue","Django"] }', () => {
    const state = parseParams(new URLSearchParams('tech=Vue,Django'))
    expect(state.tech).toEqual(['Vue', 'Django'])
  })

  it('Given ?tech=Vue&seniority=senior Then both dims are set', () => {
    const state = parseParams(new URLSearchParams('tech=Vue&seniority=senior'))
    expect(state.tech).toEqual(['Vue'])
    expect(state.seniority).toEqual(['senior'])
  })

  it('Given ?seniority=invalid Then seniority is empty (sanitized)', () => {
    const state = parseParams(new URLSearchParams('seniority=invalid'))
    expect(state.seniority).toEqual([])
  })

  it('Given ?seniority=senior,invalid,lead Then only valid values kept', () => {
    const state = parseParams(
      new URLSearchParams('seniority=senior,invalid,lead'),
    )
    expect(state.seniority).toEqual(['senior', 'lead'])
  })

  it('Given ?type=web,ai Then projectType has those values', () => {
    const state = parseParams(new URLSearchParams('type=web,ai'))
    expect(state.projectType).toEqual(['web', 'ai'])
  })

  it('Given ?type=invalid Then projectType is empty', () => {
    const state = parseParams(new URLSearchParams('type=invalid'))
    expect(state.projectType).toEqual([])
  })

  it('Given ?skills=technical Then skills is ["technical"]', () => {
    const state = parseParams(new URLSearchParams('skills=technical'))
    expect(state.skills).toEqual(['technical'])
  })

  it('Given ?skills=technical,soft Then skills has both', () => {
    const state = parseParams(new URLSearchParams('skills=technical,soft'))
    expect(state.skills).toEqual(['technical', 'soft'])
  })

  it('Given ?skills=invalid Then skills is empty', () => {
    const state = parseParams(new URLSearchParams('skills=invalid'))
    expect(state.skills).toEqual([])
  })

  it('Given ?from=2022-01&to=2026-05 Then from/to are set', () => {
    const state = parseParams(new URLSearchParams('from=2022-01&to=2026-05'))
    expect(state.from).toBe('2022-01')
    expect(state.to).toBe('2026-05')
  })

  it('Given ?from=invalid Then from is empty', () => {
    const state = parseParams(new URLSearchParams('from=invalid'))
    expect(state.from).toBe('')
  })

  it('Given ?from=2022-13 Then from is empty (invalid month)', () => {
    const state = parseParams(new URLSearchParams('from=2022-13'))
    expect(state.from).toBe('')
  })

  it('Given ?hideConfidential=1 Then hideConfidential is true', () => {
    const state = parseParams(new URLSearchParams('hideConfidential=1'))
    expect(state.hideConfidential).toBe(true)
  })

  it('Given ?hideConfidential=true Then hideConfidential is true', () => {
    const state = parseParams(new URLSearchParams('hideConfidential=true'))
    expect(state.hideConfidential).toBe(true)
  })

  it('Given ?hideConfidential=0 Then hideConfidential is false', () => {
    const state = parseParams(new URLSearchParams('hideConfidential=0'))
    expect(state.hideConfidential).toBe(false)
  })

  it('Given no hideConfidential param Then hideConfidential is false', () => {
    const state = parseParams(new URLSearchParams(''))
    expect(state.hideConfidential).toBe(false)
  })

  it('Given ?tech= (empty value) Then tech is empty', () => {
    const state = parseParams(new URLSearchParams('tech='))
    expect(state.tech).toEqual([])
  })

  it('Given ?tech=Vue,,Django Then empty entries filtered out', () => {
    const state = parseParams(new URLSearchParams('tech=Vue,,Django'))
    expect(state.tech).toEqual(['Vue', 'Django'])
  })

  it('Given ?tech=%20Vue%20 Then trim whitespace', () => {
    const state = parseParams(new URLSearchParams('tech=%20Vue%20'))
    expect(state.tech).toEqual(['Vue'])
  })

  it('Given full URL with all dims Then full state is parsed', () => {
    const state = parseParams(
      new URLSearchParams(
        'tech=Vue,Django&seniority=senior,lead&type=web&skills=technical&from=2022-01&to=2026-05&hideConfidential=1',
      ),
    )
    expect(state).toEqual({
      tech: ['Vue', 'Django'],
      seniority: ['senior', 'lead'],
      projectType: ['web'],
      skills: ['technical'],
      from: '2022-01',
      to: '2026-05',
      hideConfidential: true,
    })
  })
})

describe('serializeState (inverse of parseParams) [AC-11, AC-13]', () => {
  it('Given empty state Then returns empty string', () => {
    expect(serializeState(emptyFilterState())).toBe('')
  })

  it('Given state with tech only Then returns ?tech=Vue,Django', () => {
    const result = serializeState({
      ...emptyFilterState(),
      tech: ['Vue', 'Django'],
    })
    expect(result).toBe('tech=Vue%2CDjango')
  })

  it('Given full state Then preserves all dimensions', () => {
    const result = serializeState({
      tech: ['Vue'],
      seniority: ['senior'],
      projectType: ['web'],
      skills: ['technical'],
      from: '2022-01',
      to: '2026-05',
      hideConfidential: true,
    })
    expect(result).toContain('tech=Vue')
    expect(result).toContain('seniority=senior')
    expect(result).toContain('type=web')
    expect(result).toContain('skills=technical')
    expect(result).toContain('from=2022-01')
    expect(result).toContain('to=2026-05')
    expect(result).toContain('hideConfidential=1')
  })

  it('Given state Then parse(serialize(state)) === state (round-trip)', () => {
    const original = {
      tech: ['Vue', 'Django'],
      seniority: ['senior'],
      projectType: ['web', 'ai'],
      skills: ['technical'],
      from: '2022-01',
      to: '2026-05',
      hideConfidential: true,
    }
    const serialized = serializeState(original)
    const restored = parseParams(new URLSearchParams(serialized))
    expect(restored).toEqual(original)
  })
})
