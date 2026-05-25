/**
 * @description Tests para cv-detail: decide el nivel de detalle del CV
 *   segun el niche. El CV generico muestra todo; los niches un subset.
 */
import { describe, expect, it } from 'vitest'
import {
  isDetailedCv,
  NICHE_RESPONSIBILITIES_LIMIT,
  visibleResponsibilities,
} from '../../../src/lib/cv-detail'

describe('isDetailedCv', () => {
  it('Given niche generic When isDetailedCv Then retorna true', () => {
    expect(isDetailedCv('generic')).toBe(true)
  })

  it('Given niche architect When isDetailedCv Then retorna false', () => {
    expect(isDetailedCv('architect')).toBe(false)
  })

  it('Given niche fintech When isDetailedCv Then retorna false', () => {
    expect(isDetailedCv('fintech')).toBe(false)
  })

  it('Given niche leader When isDetailedCv Then retorna false', () => {
    expect(isDetailedCv('leader')).toBe(false)
  })

  it('Given niche vibe When isDetailedCv Then retorna false', () => {
    expect(isDetailedCv('vibe')).toBe(false)
  })
})

describe('visibleResponsibilities', () => {
  const items = ['a', 'b', 'c', 'd', 'e']

  it('Given 5 items y niche generic When visibleResponsibilities Then retorna los 5 sin recorte', () => {
    expect(visibleResponsibilities(items, 'generic')).toStrictEqual([
      'a',
      'b',
      'c',
      'd',
      'e',
    ])
  })

  it('Given 5 items y niche fintech When visibleResponsibilities Then retorna los primeros 3', () => {
    expect(visibleResponsibilities(items, 'fintech')).toStrictEqual([
      'a',
      'b',
      'c',
    ])
  })

  it('Given 2 items y niche architect When visibleResponsibilities Then retorna los 2 (menos que el limite)', () => {
    expect(visibleResponsibilities(['x', 'y'], 'architect')).toStrictEqual([
      'x',
      'y',
    ])
  })

  it('Given lista vacia When visibleResponsibilities Then retorna lista vacia para cualquier niche', () => {
    expect(visibleResponsibilities([], 'generic')).toStrictEqual([])
    expect(visibleResponsibilities([], 'leader')).toStrictEqual([])
  })

  it('Given el limite de niche When se inspecciona NICHE_RESPONSIBILITIES_LIMIT Then vale 3', () => {
    expect(NICHE_RESPONSIBILITIES_LIMIT).toBe(3)
  })
})
