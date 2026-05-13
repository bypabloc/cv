/**
 * @function sortByPriority
 * @description Ordena entries por `priority[niche]` descendente. Entries
 *   sin priority para ese nicho van al final, preservando orden relativo
 *   (sort estable de JS).
 *
 * @param items - Array de entries con propiedad `priority: PriorityByNiche`
 * @param niche - Nicho cuya prioridad se usa para ordenar
 * @returns Nuevo array ordenado (no muta el input)
 *
 * @example
 *   sortByPriority(experiences, 'fintech')
 *     // → entries de fintech ordenadas por priority.fintech desc,
 *     //   las que no tienen priority.fintech al final
 */
import type { Niche, PriorityByNiche } from '../schemas'

interface WithPriority {
  priority: PriorityByNiche
}

export function sortByPriority<T extends WithPriority>(
  items: readonly T[],
  niche: Niche,
): T[] {
  const indexed = items.map((item, index) => ({ item, index }))
  indexed.sort((a, b) => {
    const pa = a.item.priority[niche]
    const pb = b.item.priority[niche]
    if (pa === undefined && pb === undefined) return a.index - b.index
    if (pa === undefined) return 1
    if (pb === undefined) return -1
    if (pa !== pb) return pb - pa
    return a.index - b.index
  })
  return indexed.map((x) => x.item)
}
