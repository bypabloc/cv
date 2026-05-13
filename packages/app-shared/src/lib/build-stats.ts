/**
 * @module build-stats
 * @description Deriva stats numericos del CV (years, companies, countries,
 *   certifications) para StatsBar. Prioriza valores declarados en
 *   profile.stats; si no existen, calcula desde experiences[] y certificates[].
 */
import {
  certificates,
  type Experience,
  experiences,
  type Profile,
  type ProfileStats,
  profile,
} from '@portfolio/content'

const DEFAULT_COUNTRIES = 4

/**
 * @function calcYearsExperience
 * @description Calcula years of experience desde la fecha de inicio mas antigua.
 *
 * @param {readonly Experience[]} list - Lista de experiencias a analizar
 * @returns {number} Anos completos desde el primer rol al momento actual
 *
 * @example
 *   calcYearsExperience([{ start: '2013-01', ... }])  // 13
 *   calcYearsExperience([])  // 0
 */
export function calcYearsExperience(list: readonly Experience[]): number {
  if (list.length === 0) {
    return 0
  }
  const starts = list.map((e) => e.start).sort((a, b) => a.localeCompare(b))
  // starts[0] siempre existe porque list.length > 0 (guard arriba)
  const earliestStr = starts[0] as string
  const [yearStr, monthStr] = earliestStr.split('-')
  const earliest = new Date(Number(yearStr), Number(monthStr) - 1, 1)
  const now = new Date()
  const diffYears =
    now.getFullYear() -
    earliest.getFullYear() +
    (now.getMonth() - earliest.getMonth()) / 12
  return Math.max(0, Math.floor(diffYears))
}

/**
 * @function countCompanies
 * @description Cuenta companias unicas en la lista de experiences (por
 *   `company` field).
 *
 * @param {readonly Experience[]} list - Lista de experiencias
 * @returns {number} Conteo de companias unicas
 */
export function countCompanies(list: readonly Experience[]): number {
  return new Set(list.map((e) => e.company)).size
}

/**
 * @function buildStats
 * @description Construye stats finales para StatsBar. Si profile.stats existe,
 *   usa esos valores; si no, calcula desde data.
 *
 * @param {Profile} [p=profile] - Profile singleton (default: imported profile)
 * @returns {ProfileStats} Stats listos para renderizar
 *
 * @example
 *   const stats = buildStats()
 *   // { yearsExperience: 12, companies: 5, countries: 4, certifications: 11 }
 */
export function buildStats(p: Profile = profile): ProfileStats {
  if (p.stats) {
    return p.stats
  }
  return {
    yearsExperience: calcYearsExperience(experiences),
    companies: countCompanies(experiences),
    countries: DEFAULT_COUNTRIES,
    certifications: certificates.length,
  }
}
