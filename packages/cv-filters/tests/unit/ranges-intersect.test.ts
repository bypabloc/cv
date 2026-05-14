/**
 * @description Tests para rangesIntersect(). Cubre AC-6 (rango fechas).
 *
 *   Semantica: dos rangos [a1, a2] y [b1, b2] intersectan si
 *   max(a1,b1) <= min(a2,b2). Maneja "open end" (en === '') como "presente"
 *   (Number.POSITIVE_INFINITY).
 */
import { describe, expect, it } from 'vitest'
import { rangesIntersect } from '../../src/ranges-intersect'

describe('rangesIntersect [AC-6]', () => {
  it('Given two identical ranges Then they intersect', () => {
    expect(
      rangesIntersect(
        { start: '2024-01', end: '2024-12' },
        { start: '2024-01', end: '2024-12' },
      ),
    ).toBe(true)
  })

  it('Given fully overlapping ranges Then they intersect', () => {
    expect(
      rangesIntersect(
        { start: '2022-01', end: '2026-05' },
        { start: '2024-01', end: '2024-12' },
      ),
    ).toBe(true)
  })

  it('Given partially overlapping (left) Then they intersect', () => {
    expect(
      rangesIntersect(
        { start: '2020-01', end: '2023-06' },
        { start: '2022-01', end: '2024-12' },
      ),
    ).toBe(true)
  })

  it('Given partially overlapping (right) Then they intersect', () => {
    expect(
      rangesIntersect(
        { start: '2024-01', end: '2026-12' },
        { start: '2022-01', end: '2024-12' },
      ),
    ).toBe(true)
  })

  it('Given completely disjoint ranges (gap) Then they do NOT intersect', () => {
    expect(
      rangesIntersect(
        { start: '2020-01', end: '2021-12' },
        { start: '2024-01', end: '2026-12' },
      ),
    ).toBe(false)
  })

  it('Given ranges touching at boundary Then they intersect (inclusive)', () => {
    expect(
      rangesIntersect(
        { start: '2020-01', end: '2024-01' },
        { start: '2024-01', end: '2026-12' },
      ),
    ).toBe(true)
  })

  it('Given item with no end (open, presente) and filter range Then they intersect when start <= filter.end', () => {
    expect(
      rangesIntersect(
        { start: '2022-08', end: '' },
        { start: '2024-01', end: '2026-05' },
      ),
    ).toBe(true)
  })

  it('Given item with no end and filter end empty Then they intersect (both open)', () => {
    expect(
      rangesIntersect(
        { start: '2022-08', end: '' },
        { start: '2024-01', end: '' },
      ),
    ).toBe(true)
  })

  it('Given filter with no from (empty start) and item ends before Then no intersection only if filter.to < item.start', () => {
    // filter [_, 2021-12], item [2022-08, _]: filter ends before item starts -> no intersect
    expect(
      rangesIntersect(
        { start: '2022-08', end: '' },
        { start: '', end: '2021-12' },
      ),
    ).toBe(false)
  })

  it('Given filter open both sides Then any item intersects', () => {
    expect(
      rangesIntersect(
        { start: '2020-01', end: '2020-12' },
        { start: '', end: '' },
      ),
    ).toBe(true)
  })

  it('Given item starts after filter ends Then no intersection', () => {
    expect(
      rangesIntersect(
        { start: '2026-01', end: '2026-12' },
        { start: '2020-01', end: '2024-12' },
      ),
    ).toBe(false)
  })

  it('Given item with same start and end (single month) inside filter Then they intersect', () => {
    expect(
      rangesIntersect(
        { start: '2024-06', end: '2024-06' },
        { start: '2024-01', end: '2024-12' },
      ),
    ).toBe(true)
  })

  it('Given item with no start Then treated as -infinity (always intersects forward filter)', () => {
    expect(
      rangesIntersect(
        { start: '', end: '2020-12' },
        { start: '2018-01', end: '2026-12' },
      ),
    ).toBe(true)
  })
})
