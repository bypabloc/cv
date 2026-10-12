/**
 * @function sortByDateDesc
 * @description Orden cronologico inverso: `start` mas reciente primero; a
 *   igual `start`, la entry vigente (sin `end`) o la que termino despues.
 *
 * @param items - Entries con `start` (YYYY-MM) y `end` opcional
 * @returns Nuevo array ordenado (no muta el input)
 *
 * @example
 *   sortByDateDesc(experiences) // Destacame 2022 → ... → Corpoelec 2013
 */
interface WithDates {
  start: string
  end?: string
}

export function sortByDateDesc<T extends WithDates>(items: readonly T[]): T[] {
  return [...items].sort(
    (a, b) =>
      b.start.localeCompare(a.start) ||
      (b.end ?? '9999').localeCompare(a.end ?? '9999'),
  )
}
