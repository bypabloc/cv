/**
 * @module cv-filters/ranges-intersect
 * @description Detecta si dos rangos de fechas YYYY-MM intersectan.
 *   Maneja rangos abiertos (start o end vacio).
 */

export interface DateRange {
  /** YYYY-MM o '' (sin limite inferior, treated as -infinity). */
  start: string
  /** YYYY-MM o '' (sin limite superior, treated as +infinity / presente). */
  end: string
}

/**
 * Convierte YYYY-MM a numero comparable (ej. "2024-01" -> 202401). String
 * vacio se sustituye por el sentinel pasado (para extremos abiertos).
 */
function toNumeric(value: string, openSentinel: number): number {
  if (value === '') {
    return openSentinel
  }
  const [year, month] = value.split('-')
  // year y month ya estan validados por parseYearMonth aguas arriba.
  return Number(year) * 100 + Number(month)
}

/**
 * Verdadero si los dos rangos comparten al menos un mes.
 *
 * Algoritmo: max(start1, start2) <= min(end1, end2). Inclusive en ambos
 * extremos.
 *
 * @example
 *   rangesIntersect(
 *     { start: '2022-01', end: '2024-12' },
 *     { start: '2024-01', end: '2026-05' },
 *   ) // true: comparten 2024-01..2024-12
 */
export function rangesIntersect(a: DateRange, b: DateRange): boolean {
  const aStart = toNumeric(a.start, Number.NEGATIVE_INFINITY)
  const aEnd = toNumeric(a.end, Number.POSITIVE_INFINITY)
  const bStart = toNumeric(b.start, Number.NEGATIVE_INFINITY)
  const bEnd = toNumeric(b.end, Number.POSITIVE_INFINITY)
  return Math.max(aStart, bStart) <= Math.min(aEnd, bEnd)
}
