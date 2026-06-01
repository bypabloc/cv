/**
 * @module format/date
 * @description Formateo de fechas con Intl (locale es por defecto). Sin libs.
 */

/**
 * @function formatDate
 * @description Formatea un ISO string o Date a "DD MMM YYYY, HH:mm".
 * @param {string | Date | null | undefined} value - Fecha ISO o Date
 * @param {string} locale - BCP 47 locale (default 'es')
 * @returns {string} Fecha legible, o '-' si value es nulo/invalido
 * @example
 *   formatDate('2026-05-27T10:30:00Z')  // "27 may 2026, 10:30" (segun TZ)
 */
export function formatDate(
  value: string | Date | null | undefined,
  locale = 'es',
): string {
  if (!value) return '-'
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

/**
 * @function relativeTime
 * @description Tiempo relativo legible ("hace 5 min", "hace 2 d").
 * @param {string | Date | null | undefined} value - Fecha ISO o Date
 * @param {string} locale - BCP 47 locale (default 'es')
 * @returns {string} Texto relativo, o '-' si value es nulo/invalido
 * @example
 *   relativeTime(new Date(Date.now() - 60000))  // "hace 1 min"
 */
export function relativeTime(
  value: string | Date | null | undefined,
  locale = 'es',
): string {
  if (!value) return '-'
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return '-'
  const diffMs = date.getTime() - Date.now()
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
  // [divisor en ms para esa unidad, limite superior (excl) en ms, unidad].
  // Se elige la primera unidad cuyo `abs` cae por debajo de su limite y se
  // divide por el divisor de ESA unidad.
  const divisions: [number, number, Intl.RelativeTimeFormatUnit][] = [
    [1_000, 60_000, 'second'],
    [60_000, 3_600_000, 'minute'],
    [3_600_000, 86_400_000, 'hour'],
    [86_400_000, 604_800_000, 'day'],
    [604_800_000, 2_629_800_000, 'week'],
    [2_629_800_000, 31_557_600_000, 'month'],
    [31_557_600_000, Number.POSITIVE_INFINITY, 'year'],
  ]
  const abs = Math.abs(diffMs)
  for (const [divisor, limit, unit] of divisions) {
    if (abs < limit) {
      return rtf.format(Math.round(diffMs / divisor), unit)
    }
  }
  return rtf.format(Math.round(diffMs / 31_557_600_000), 'year')
}
