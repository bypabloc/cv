/**
 * @description Tests para buildStats: derivacion de stats desde profile o
 *   calculo desde data si profile.stats no esta definido.
 */
import {
  certificates,
  type Experience,
  experiences,
  type Profile,
  profile,
} from '@portfolio/content'
import { describe, expect, it } from 'vitest'
import {
  buildStats,
  calcYearsExperience,
  countCompanies,
} from '../../../src/lib/build-stats'

const baseProfile: Profile = {
  name: 'Test',
  handle: 'test',
  headline: { es: 'h-es', en: 'h-en' },
  summary: { es: 's-es', en: 's-en' },
  location: 'Lima',
  contacts: {
    email: 'a@b.com',
    linkedin: 'https://linkedin.com/in/test',
    github: 'https://github.com/test',
  },
  avatarUrl: 'https://example.com/a.jpg',
  niches: ['generic'],
}

describe('buildStats', () => {
  it('Given profile con stats explicitos When buildStats Then retorna esos stats sin recalcular', () => {
    const profileWithStats: Profile = {
      ...baseProfile,
      stats: {
        yearsExperience: 15,
        companies: 9,
        countries: 5,
        certifications: 20,
      },
    }
    const result = buildStats(profileWithStats)
    expect(result).toStrictEqual({
      yearsExperience: 15,
      companies: 9,
      countries: 5,
      certifications: 20,
    })
  })

  it('Given profile con stats yearsExperience=0 When buildStats Then retorna 0 (no fallback)', () => {
    const profileWithStats: Profile = {
      ...baseProfile,
      stats: {
        yearsExperience: 0,
        companies: 0,
        countries: 0,
        certifications: 0,
      },
    }
    const result = buildStats(profileWithStats)
    expect(result.yearsExperience).toBe(0)
    expect(result.companies).toBe(0)
    expect(result.countries).toBe(0)
    expect(result.certifications).toBe(0)
  })

  it('Given profile sin stats When buildStats Then retorna objeto con 4 claves exactas', () => {
    const profileWithoutStats: Profile = { ...baseProfile, stats: undefined }
    const result = buildStats(profileWithoutStats)
    expect(Object.keys(result).sort()).toStrictEqual([
      'certifications',
      'companies',
      'countries',
      'yearsExperience',
    ])
  })

  it('Given profile sin stats When buildStats Then countries siempre es 4 (default declarado)', () => {
    const profileWithoutStats: Profile = { ...baseProfile, stats: undefined }
    const result = buildStats(profileWithoutStats)
    expect(result.countries).toBe(4)
  })

  it('Given profile sin stats When buildStats Then companies refleja experiences unicas (5: Destacame, Dibal, GoodMeal, Independiente/Academico, Laboratorio Cofasa)', () => {
    const profileWithoutStats: Profile = { ...baseProfile, stats: undefined }
    const result = buildStats(profileWithoutStats)
    // experiences.ts tiene 9 roles agrupados en 5 companias unicas
    expect(result.companies).toBe(5)
  })

  it('Given profile sin stats When buildStats Then certifications coincide con array certificates', () => {
    const profileWithoutStats: Profile = { ...baseProfile, stats: undefined }
    const result = buildStats(profileWithoutStats)
    // certificates.ts tiene 11 entradas segun el CV
    expect(result.certifications).toBe(11)
  })

  it('Given profile sin stats When buildStats Then yearsExperience es 12 o 13 (basado en earliest 2013-01)', () => {
    // Cubre la rama de calculo dinamico via Date.now(). Asercion exacta
    // contra el valor calculado en este momento del tiempo.
    const profileWithoutStats: Profile = { ...baseProfile, stats: undefined }
    const result = buildStats(profileWithoutStats)
    const now = new Date()
    const expected = Math.floor(
      now.getFullYear() - 2013 + (now.getMonth() - 0) / 12,
    )
    expect(result.yearsExperience).toBe(expected)
  })
})

describe('calcYearsExperience', () => {
  it('Given lista vacia When calcYearsExperience Then retorna 0', () => {
    expect(calcYearsExperience([])).toBe(0)
  })

  it('Given una sola experience con start 2020-01 When calcYearsExperience Then retorna anos desde 2020-01', () => {
    const exp = {
      slug: 'test',
      role: { es: 'r', en: 'r' },
      company: 'C',
      start: '2020-01' as const,
      niches: ['generic'],
      priority: {},
      responsibilities: { es: ['x'], en: ['x'] },
      achievements: { es: [], en: [] },
      skillsTechnical: [],
      skillsSoft: [],
    } as unknown as Experience
    const result = calcYearsExperience([exp])
    const now = new Date()
    const expected = Math.floor(
      now.getFullYear() - 2020 + (now.getMonth() - 0) / 12,
    )
    expect(result).toBe(expected)
  })
})

describe('countCompanies', () => {
  it('Given lista vacia When countCompanies Then retorna 0', () => {
    expect(countCompanies([])).toBe(0)
  })

  it('Given 3 experiences con 2 companies distintas When countCompanies Then retorna 2', () => {
    const make = (company: string): Experience =>
      ({
        slug: 's',
        role: { es: 'r', en: 'r' },
        company,
        start: '2020-01' as const,
        niches: ['generic'],
        priority: {},
        responsibilities: { es: ['x'], en: ['x'] },
        achievements: { es: [], en: [] },
        skillsTechnical: [],
        skillsSoft: [],
      }) as unknown as Experience
    const list = [make('A'), make('A'), make('B')]
    expect(countCompanies(list)).toBe(2)
  })
})

describe('profile real: consistencia de stats con la data', () => {
  it('Given el profile real When se lee stats.companies Then vale 5 (empresas distintas en experiences)', () => {
    // Las 9 experiencias agrupan 5 nombres de empresa distintos.
    expect(profile.stats?.companies).toBe(5)
    expect(profile.stats?.companies).toBe(countCompanies(experiences))
  })

  it('Given el profile real When se lee stats.certifications Then coincide con la cantidad de certificates', () => {
    expect(profile.stats?.certifications).toBe(certificates.length)
    expect(profile.stats?.certifications).toBe(11)
  })

  it('Given el profile real When se lee stats.yearsExperience Then vale 12', () => {
    expect(profile.stats?.yearsExperience).toBe(12)
  })

  it('Given el profile real When se lee el summary Then menciona "12 años" y NO "8 años"', () => {
    expect(profile.summary.es).toContain('12 años')
    expect(profile.summary.es).not.toContain('8 años')
  })

  it('Given el profile real When se lee el summary en ingles Then menciona "12 years" y NO "8 years"', () => {
    expect(profile.summary.en).toContain('12 years')
    expect(profile.summary.en).not.toContain('8 years')
  })
})
