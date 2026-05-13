/**
 * @description Tests para filterByNiche. Cubre AC-6, AC-7.
 */
import { describe, expect, it } from 'vitest'
import { filterByNiche } from '../../src/lib/filter-by-niche'
import type { Niche } from '../../src/schemas'

interface Item {
  id: string
  niches: Niche[]
}

const items: Item[] = [
  { id: 'a', niches: ['fintech', 'generic'] },
  { id: 'b', niches: ['architect', 'generic'] },
  { id: 'c', niches: ['vibe'] },
  { id: 'd', niches: ['fintech', 'architect', 'leader', 'vibe', 'generic'] },
]

describe('filterByNiche', () => {
  it('Given items with niches When filter "fintech" Then returns only fintech entries', () => {
    const result = filterByNiche(items, 'fintech')
    expect(result.map((i) => i.id)).toEqual(['a', 'd'])
  })

  it('Given items with niches When filter "vibe" Then returns only vibe entries', () => {
    const result = filterByNiche(items, 'vibe')
    expect(result.map((i) => i.id)).toEqual(['c', 'd'])
  })

  it('Given items with niches When filter "generic" Then returns 3 entries (a,b,d)', () => {
    const result = filterByNiche(items, 'generic')
    expect(result.map((i) => i.id)).toEqual(['a', 'b', 'd'])
  })

  it('Given items with niches When filter "leader" Then returns only d', () => {
    const result = filterByNiche(items, 'leader')
    expect(result.map((i) => i.id)).toEqual(['d'])
  })

  it('Given empty array When filter any niche Then returns empty array', () => {
    expect(filterByNiche([], 'fintech')).toEqual([])
  })

  it('Given items When filter Then does not mutate input array', () => {
    const original = [...items]
    filterByNiche(items, 'fintech')
    expect(items).toEqual(original)
  })
})
