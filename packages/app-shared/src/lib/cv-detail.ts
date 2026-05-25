/**
 * @module cv-detail
 * @description Decide el nivel de detalle del CV segun el niche. El CV
 *   generico (`niche === 'generic'`) muestra el detalle completo de cada
 *   experiencia (todas las responsabilidades + los logros); los CV de
 *   nicho muestran un subset acotado.
 */
import type { Niche } from '@portfolio/content'

/**
 * Maximo de responsabilidades visibles en un CV de nicho. El CV generico
 * no aplica este recorte (muestra todas).
 */
export const NICHE_RESPONSIBILITIES_LIMIT = 3

/**
 * @function isDetailedCv
 * @description True si el CV debe mostrar el detalle completo de cada
 *   experiencia (responsabilidades sin recorte + seccion de logros). Solo
 *   el CV generico es detallado; los 4 niches muestran el subset.
 *
 * @param {Niche} niche - Niche del CV en render
 *
 * @returns {boolean} true si es el CV generico, false para un niche
 *
 * @example
 *   isDetailedCv('generic')    // true
 *   isDetailedCv('architect')  // false
 */
export function isDetailedCv(niche: Niche): boolean {
  return niche === 'generic'
}

/**
 * @function visibleResponsibilities
 * @description Responsabilidades a renderizar segun el niche: todas para
 *   el CV generico, las primeras NICHE_RESPONSIBILITIES_LIMIT para un
 *   CV de nicho.
 *
 * @param {readonly string[]} items - Responsabilidades de la experiencia
 * @param {Niche} niche - Niche del CV en render
 *
 * @returns {readonly string[]} Subconjunto a mostrar
 *
 * @example
 *   visibleResponsibilities(['a','b','c','d'], 'generic')  // ['a','b','c','d']
 *   visibleResponsibilities(['a','b','c','d'], 'fintech')  // ['a','b','c']
 */
export function visibleResponsibilities(
  items: readonly string[],
  niche: Niche,
): readonly string[] {
  return isDetailedCv(niche)
    ? items
    : items.slice(0, NICHE_RESPONSIBILITIES_LIMIT)
}
