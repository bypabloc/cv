/**
 * @function formatYearMonth
 * @description Formatea una fecha YYYY-MM al nombre del mes + año según locale.
 *   Lanza Error si el input no matchea YYYY-MM válido o el mes está fuera de 1-12.
 *
 * @param input - Fecha en formato YYYY-MM (ej. "2024-01")
 * @param locale - 'es' (default) o 'en'
 * @returns Mes + año legible (ej. "enero 2024" / "January 2024")
 *
 * @example
 *   formatYearMonth('2024-01', 'es')  // "enero 2024"
 *   formatYearMonth('2024-12', 'en')  // "December 2024"
 */
export function formatYearMonth(
  input: string,
  locale: 'es' | 'en' = 'es',
): string {
  const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(input)
  if (!match) {
    throw new Error(`Invalid YYYY-MM input: "${input}"`)
  }
  const year = match[1]
  const month = Number.parseInt(match[2] as string, 10)
  const date = new Date(Date.UTC(Number(year), month - 1, 1))
  const formatter = new Intl.DateTimeFormat(
    locale === 'es' ? 'es-ES' : 'en-US',
    {
      month: 'long',
      year: 'numeric',
      timeZone: 'UTC',
    },
  )
  return formatter.format(date)
}

/**
 * @function formatRange
 * @description Formatea un rango "start → end" devolviendo "Presente"/"Present" si end es undefined.
 *
 * @example
 *   formatRange('2022-08', undefined, 'es')  // "agosto 2022 — Presente"
 *   formatRange('2021-12', '2022-08', 'en')  // "December 2021 — August 2022"
 */
export function formatRange(
  start: string,
  end: string | undefined,
  locale: 'es' | 'en' = 'es',
): string {
  const startFmt = formatYearMonth(start, locale)
  const endFmt = end
    ? formatYearMonth(end, locale)
    : locale === 'es'
      ? 'Presente'
      : 'Present'
  return `${startFmt} — ${endFmt}`
}
