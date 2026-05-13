/**
 * @description Tests para sortByPriority. Cubre AC-6.
 */
import { describe, expect, it } from 'vitest'
import { sortByPriority } from '../../src/lib/sort-by-priority'
import type { PriorityByNiche } from '../../src/schemas'

interface Item {
  id: string
  priority: PriorityByNiche
}

describe('sortByPriority', () => {
  it('Given items with priority When sort by fintech Then returns desc order', () => {
    const items: Item[] = [
      { id: 'low', priority: { fintech: 10 } },
      { id: 'high', priority: { fintech: 100 } },
      { id: 'mid', priority: { fintech: 50 } },
    ]
    const result = sortByPriority(items, 'fintech')
    expect(result.map((i) => i.id)).toEqual(['high', 'mid', 'low'])
  })

  it('Given items without priority for niche When sort Then those go last preserving input order', () => {
    const items: Item[] = [
      { id: 'noprio-1', priority: {} },
      { id: 'high', priority: { fintech: 100 } },
      { id: 'noprio-2', priority: { architect: 50 } },
      { id: 'mid', priority: { fintech: 50 } },
    ]
    const result = sortByPriority(items, 'fintech')
    expect(result.map((i) => i.id)).toEqual([
      'high',
      'mid',
      'noprio-1',
      'noprio-2',
    ])
  })

  it('Given items with equal priority When sort Then preserves input order (stable)', () => {
    const items: Item[] = [
      { id: 'a', priority: { fintech: 50 } },
      { id: 'b', priority: { fintech: 50 } },
      { id: 'c', priority: { fintech: 50 } },
    ]
    const result = sortByPriority(items, 'fintech')
    expect(result.map((i) => i.id)).toEqual(['a', 'b', 'c'])
  })

  it('Given empty array When sort Then returns empty array', () => {
    expect(sortByPriority([], 'fintech')).toEqual([])
  })

  it('Given items When sort Then does not mutate input array', () => {
    const items: Item[] = [
      { id: 'a', priority: { fintech: 10 } },
      { id: 'b', priority: { fintech: 50 } },
    ]
    const original = [...items]
    sortByPriority(items, 'fintech')
    expect(items).toEqual(original)
  })
})
