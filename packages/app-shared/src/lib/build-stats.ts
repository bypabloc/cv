/**
 * @module build-stats
 * @description Deriva stats numericos del CV (years, companies, countries,
 *   certifications) para StatsBar. Prioriza valores declarados en
 *   profile.stats; si no existen, calcula desde experiences[] y certificates[].
 */
import {
  certificates,
  experiences,
  type Profile,
  type ProfileStats,
  profile,
} from '@portfolio/content'

/**
 * Cuenta companias unicas desde experiences[] (slug company / company name).
 */
function countCompanies(): number {
  const unique = new Set(experiences.map((e) => e.company))
  return unique.size
}

/**
 * Calcula years of experience desde la fecha de inicio mas antigua.
 */
function calcYearsExperience(): number {
  const starts = experiences
    .map((e) => e.start)
    .sort((a, b) => a.localeCompare(b))
  if (starts.length === 0) {
    return 0
  }
  const [year, month] = (starts[0] ?? '2013-01').split('-').map(Number)
  const earliest = new Date(year ?? 2013, (month ?? 1) - 1, 1)
  const now = new Date()
  const diffYears =
    now.getFullYear() -
    earliest.getFullYear() +
    (now.getMonth() - earliest.getMonth()) / 12
  return Math.max(0, Math.floor(diffYears))
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
 *   // { yearsExperience: 12, companies: 8, countries: 4, certifications: 11 }
 */
export function buildStats(p: Profile = profile): ProfileStats {
  if (p.stats) {
    return p.stats
  }
  return {
    yearsExperience: calcYearsExperience(),
    companies: countCompanies(),
    countries: 4,
    certifications: certificates.length,
  }
}
