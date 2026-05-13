/**
 * @description Tests para formatYearMonth y formatRange.
 */
import { describe, expect, it } from 'vitest'
import { formatRange, formatYearMonth } from '../../src/lib/format-date'

describe('formatYearMonth', () => {
  it('Given "2024-01" and locale "es" When format Then returns "enero de 2024"', () => {
    expect(formatYearMonth('2024-01', 'es')).toBe('enero de 2024')
  })

  it('Given "2024-12" and locale "en" When format Then returns "December 2024"', () => {
    expect(formatYearMonth('2024-12', 'en')).toBe('December 2024')
  })

  it('Given "2022-08" and default locale When format Then returns Spanish form', () => {
    expect(formatYearMonth('2022-08')).toBe('agosto de 2022')
  })

  it('Given invalid format When format Then throws Error', () => {
    expect(() => formatYearMonth('2024/01')).toThrow(/Invalid YYYY-MM/)
    expect(() => formatYearMonth('2024-13')).toThrow(/Invalid YYYY-MM/)
    expect(() => formatYearMonth('24-01')).toThrow(/Invalid YYYY-MM/)
    expect(() => formatYearMonth('')).toThrow(/Invalid YYYY-MM/)
  })
})

describe('formatRange', () => {
  it('Given start without end and locale "es" When format Then ends with "Presente"', () => {
    expect(formatRange('2022-08', undefined, 'es')).toBe(
      'agosto de 2022 — Presente',
    )
  })

  it('Given start without end and locale "en" When format Then ends with "Present"', () => {
    expect(formatRange('2022-08', undefined, 'en')).toBe(
      'August 2022 — Present',
    )
  })

  it('Given start and end with locale "en" When format Then returns full range', () => {
    expect(formatRange('2021-12', '2022-08', 'en')).toBe(
      'December 2021 — August 2022',
    )
  })

  it('Given start and end with default locale When format Then returns Spanish range', () => {
    expect(formatRange('2018-12', '2021-09')).toBe(
      'diciembre de 2018 — septiembre de 2021',
    )
  })
})
