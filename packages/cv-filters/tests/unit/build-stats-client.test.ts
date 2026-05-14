/**
 * @description Tests para buildStatsClient(). Cubre AC-14 (recalculo dinamico
 *   de stats sobre items visibles).
 *
 *   Diferencia con build-stats (server) en @portfolio/app-shared:
 *   - El servidor lee profile.stats hardcoded si existe.
 *   - El cliente SIEMPRE deriva de los items visibles (no fallback).
 */
import { describe, expect, it } from 'vitest'
import {
  buildStatsClient,
  calcYearsFromStarts,
  countUniqueCompanies,
} from '../../src/build-stats-client'

describe('calcYearsFromStarts', () => {
  it('Given empty list Then returns 0', () => {
    expect(calcYearsFromStarts([], new Date('2026-05-13'))).toBe(0)
  })

  it('Given single start 2013-01 and now 2026-05 Then returns 13', () => {
    expect(calcYearsFromStarts(['2013-01'], new Date('2026-05-13'))).toBe(13)
  })

  it('Given multiple starts uses earliest', () => {
    expect(
      calcYearsFromStarts(
        ['2020-01', '2018-06', '2022-01'],
        new Date('2026-05-13'),
      ),
    ).toBe(7)
  })

  it('Given start 2024-06 and now 2024-12 Then returns 0 (< 1 year)', () => {
    expect(calcYearsFromStarts(['2024-06'], new Date('2024-12-13'))).toBe(0)
  })

  it('Given start in the future Then returns 0 (no negative)', () => {
    expect(calcYearsFromStarts(['2030-01'], new Date('2026-05-13'))).toBe(0)
  })

  it('Given start 2024-01 and now 2026-01 Then returns 2 (exact)', () => {
    expect(calcYearsFromStarts(['2024-01'], new Date('2026-01-13'))).toBe(2)
  })
})

describe('countUniqueCompanies', () => {
  it('Given empty list Then returns 0', () => {
    expect(countUniqueCompanies([])).toBe(0)
  })

  it('Given 3 items in 2 companies Then returns 2', () => {
    expect(countUniqueCompanies(['Acme', 'Acme', 'Beta'])).toBe(2)
  })

  it('Given 5 unique companies Then returns 5', () => {
    expect(countUniqueCompanies(['A', 'B', 'C', 'D', 'E'])).toBe(5)
  })
})

describe('buildStatsClient [AC-14]', () => {
  it('Given empty visible items Then all stats are 0', () => {
    const stats = buildStatsClient(
      { experienceStarts: [], experienceCompanies: [], certificatesCount: 0 },
      new Date('2026-05-13'),
    )
    expect(stats).toEqual({
      yearsExperience: 0,
      companies: 0,
      countries: 0,
      certifications: 0,
    })
  })

  it('Given visible items Then stats reflect them', () => {
    const stats = buildStatsClient(
      {
        experienceStarts: ['2022-01', '2024-06'],
        experienceCompanies: ['Acme', 'Beta'],
        certificatesCount: 3,
      },
      new Date('2026-05-13'),
    )
    expect(stats.yearsExperience).toBe(4)
    expect(stats.companies).toBe(2)
    expect(stats.certifications).toBe(3)
  })

  it('Given duplicate companies Then companies is unique count', () => {
    const stats = buildStatsClient(
      {
        experienceStarts: ['2022-01', '2023-01', '2024-01'],
        experienceCompanies: ['Destacame', 'Destacame', 'Acme'],
        certificatesCount: 0,
      },
      new Date('2026-05-13'),
    )
    expect(stats.companies).toBe(2)
  })

  it('Given starts produces correct years using earliest', () => {
    const stats = buildStatsClient(
      {
        experienceStarts: ['2024-01', '2018-06', '2022-08'],
        experienceCompanies: ['A', 'B', 'C'],
        certificatesCount: 0,
      },
      new Date('2026-05-13'),
    )
    expect(stats.yearsExperience).toBe(7)
  })

  it('Given client-side recalculation Then countries is always 0 (no source)', () => {
    // El cliente no tiene acceso a una lista de paises; lo deja en 0 o
    // el componente decide mostrar el default global.
    const stats = buildStatsClient(
      {
        experienceStarts: ['2020-01'],
        experienceCompanies: ['A'],
        certificatesCount: 2,
      },
      new Date('2026-05-13'),
    )
    expect(stats.countries).toBe(0)
  })
})
