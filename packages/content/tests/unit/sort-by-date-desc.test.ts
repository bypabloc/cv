import { describe, expect, it } from 'vitest'
import { sortByDateDesc } from '../../src/lib/sort-by-date-desc'

describe('sortByDateDesc', () => {
  it('Given entries con distinto start When ordenar Then el mas reciente va primero', () => {
    const items = [
      { slug: 'a', start: '2014-01', end: '2014-12' },
      { slug: 'b', start: '2022-08' },
      { slug: 'c', start: '2015-11', end: '2015-12' },
    ]

    const result = sortByDateDesc(items).map((e) => e.slug)

    expect(result).toEqual(['b', 'c', 'a'])
  })

  it('Given mismo start When ordenar Then la que sigue vigente (sin end) va primero', () => {
    const items = [
      { slug: 'cerrada', start: '2020-01', end: '2021-01' },
      { slug: 'vigente', start: '2020-01' },
    ]

    const result = sortByDateDesc(items).map((e) => e.slug)

    expect(result).toEqual(['vigente', 'cerrada'])
  })

  it('Given un array When ordenar Then no muta el input', () => {
    const items = [
      { slug: 'a', start: '2014-01' },
      { slug: 'b', start: '2022-01' },
    ]

    sortByDateDesc(items)

    expect(items.map((e) => e.slug)).toEqual(['a', 'b'])
  })
})
