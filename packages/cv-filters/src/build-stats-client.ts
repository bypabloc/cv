/**
 * @module cv-filters/build-stats-client
 * @description Recalcula stats del CV client-side a partir de los items
 *   visibles tras aplicar filtros. Pendant client del `buildStats()` de
 *   `@portfolio/app-shared`.
 *
 *   Diferencias con la version server:
 *   - No lee `profile.stats` (no hay fallback): siempre deriva.
 *   - No tiene una lista de paises: lo deja en 0 (UI decide si mostrar el
 *     valor declarado o el dinamico).
 *
 *   La inyeccion de la fecha actual via parametro permite tests deterministas.
 */

export interface ClientStatsInput {
  /** Lista de `start` (YYYY-MM) de los experiences visibles. */
  experienceStarts: string[]
  /** Lista de `company` de los experiences visibles (no necesariamente unique). */
  experienceCompanies: string[]
  /** Cantidad de certificates visibles. */
  certificatesCount: number
}

export interface ClientStats {
  yearsExperience: number
  companies: number
  countries: number
  certifications: number
}

/**
 * Calcula years of experience a partir de la fecha de inicio mas antigua.
 *
 * @param starts Lista de fechas YYYY-MM
 * @param now Fecha actual (inyectable para tests)
 * @returns Anos completos desde la fecha mas antigua hasta `now`, >= 0
 */
export function calcYearsFromStarts(
  starts: readonly string[],
  now: Date,
): number {
  if (starts.length === 0) {
    return 0
  }
  const sorted = [...starts].sort((a, b) => a.localeCompare(b))
  const earliest = sorted[0] as string
  const [yearStr, monthStr] = earliest.split('-')
  const earliestDate = new Date(Number(yearStr), Number(monthStr) - 1, 1)
  const diffYears =
    now.getFullYear() -
    earliestDate.getFullYear() +
    (now.getMonth() - earliestDate.getMonth()) / 12
  return Math.max(0, Math.floor(diffYears))
}

/** Cantidad de companias unicas en la lista. */
export function countUniqueCompanies(companies: readonly string[]): number {
  return new Set(companies).size
}

/**
 * Construye stats client-side a partir de los items visibles.
 *
 * @param input Resumen de los items visibles
 * @param now Fecha actual (inyectable para tests; default = new Date())
 * @returns Stats listos para renderizar en StatsBar
 */
export function buildStatsClient(
  input: ClientStatsInput,
  now: Date = new Date(),
): ClientStats {
  return {
    yearsExperience: calcYearsFromStarts(input.experienceStarts, now),
    companies: countUniqueCompanies(input.experienceCompanies),
    countries: 0,
    certifications: input.certificatesCount,
  }
}
