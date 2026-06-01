/**
 * @module format/duration
 * @description Formateo de duraciones en milisegundos a HH:MM:SS.
 */

/**
 * @function formatDurationMs
 * @description Convierte ms a "HH:MM:SS" (o "MM:SS" si < 1h).
 * @param {number | null | undefined} ms - Duracion en milisegundos
 * @returns {string} Duracion formateada, o "00:00" si es nulo/negativo
 * @example
 *   formatDurationMs(83000)   // "01:23"
 *   formatDurationMs(3723000) // "01:02:03"
 */
export function formatDurationMs(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || Number.isNaN(ms) || ms < 0) {
    return '00:00'
  }
  const totalSeconds = Math.floor(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const pad = (n: number) => String(n).padStart(2, '0')
  if (hours > 0) {
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
  }
  return `${pad(minutes)}:${pad(seconds)}`
}
