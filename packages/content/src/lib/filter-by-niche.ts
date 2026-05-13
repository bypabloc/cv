/**
 * @function filterByNiche
 * @description Filtra entries cuyo array `niches[]` incluya el nicho dado.
 *   Sirve para experiences, projects, certificates, publications, awards,
 *   skills (cualquier shape con `niches: Niche[]`).
 *
 * @param items - Array de entries con propiedad `niches: Niche[]`
 * @param niche - Nicho a filtrar (uno solo)
 * @returns Subset de items cuyo `niches` contiene `niche`
 *
 * @example
 *   filterByNiche(experiences, 'fintech')
 *     // → solo experiences que tienen 'fintech' en su niches[]
 */
import type { Niche } from '../schemas'

export function filterByNiche<T extends { niches: readonly Niche[] }>(
  items: readonly T[],
  niche: Niche,
): T[] {
  return items.filter((item) => item.niches.includes(niche))
}
