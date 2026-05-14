/**
 * @module cv-filters/matches-filter
 * @description Decide si un ItemAttrs satisface un FilterState.
 *
 *   Logica:
 *   - Cada dimension activa AND-ea con las demas (inter-dimension).
 *   - Dentro de una dimension multi-valor (tech, seniority, projectType,
 *     skills), OR-ea los valores permitidos (intra-dimension).
 *   - Dimensiones vacias (sin filtro) son neutras (siempre matchean).
 *
 *   Si un item NO declara una dimension (string vacio o array vacio) y el
 *   filtro la requiere, NO matchea. Ej: filtro `seniority=[senior]` sobre
 *   un item sin seniority -> no match. Esto es coherente con la semantica
 *   "el usuario pidio explicitamente senior, no muestres lo que no es".
 *
 *   Excepcion: skills. Si el filtro `skills=[technical]` se aplica a un
 *   item que NO declara skillKind (ej. una experience), debe ignorarse el
 *   filtro para ese item (la dim solo aplica a SkillCategory). Esa
 *   distincion vive en `apply-filters.ts`, no aqui: aqui simplemente no
 *   matchea, y `apply-filters` decide a que items aplicar skill filter.
 */

import { rangesIntersect } from './ranges-intersect'
import type { FilterState, ItemAttrs } from './types'

/** Match OR: alguno de los valores del filtro esta en los valores del item. */
function matchesAnyOf(itemValues: string[], filterValues: string[]): boolean {
  if (filterValues.length === 0) {
    return true
  }
  return filterValues.some((fv) => itemValues.includes(fv))
}

/** Match exact: el valor unico del item esta en la lista de filtro. */
function matchesValueIn(itemValue: string, filterValues: string[]): boolean {
  if (filterValues.length === 0) {
    return true
  }
  if (itemValue === '') {
    return false
  }
  return filterValues.includes(itemValue)
}

/**
 * Verdadero si el item satisface todos los filtros activos del state.
 */
export function matchesFilter(item: ItemAttrs, state: FilterState): boolean {
  // tech: OR intra (cualquiera matchea)
  if (!matchesAnyOf(item.tech, state.tech)) {
    return false
  }

  // seniority: valor unico contra lista
  if (!matchesValueIn(item.seniority, state.seniority)) {
    return false
  }

  // projectType: valor unico contra lista
  if (!matchesValueIn(item.projectType, state.projectType)) {
    return false
  }

  // skills (skillKind): valor unico contra lista
  if (!matchesValueIn(item.skillKind, state.skills)) {
    return false
  }

  // fechas: rangos intersectan
  if (state.from !== '' || state.to !== '') {
    const intersects = rangesIntersect(
      { start: item.start, end: item.end },
      { start: state.from, end: state.to },
    )
    if (!intersects) {
      return false
    }
  }

  // confidential toggle
  if (state.hideConfidential && item.confidential) {
    return false
  }

  return true
}
