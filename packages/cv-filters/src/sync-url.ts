/**
 * @module cv-filters/sync-url
 * @description Lee/escribe el FilterState desde/hacia la URL del navegador.
 *
 *   - `readUrl()`: parsea `window.location.search` con `parseParams`.
 *   - `syncUrl(state)`: actualiza la URL via `history.replaceState`, sin
 *     recargar. Preserva pathname y hash, solo modifica el query string.
 *
 *   Usar `replaceState` (NO `pushState`) porque cambiar filtros no genera
 *   entrada en el history del browser (no quiero contaminar el back/forward
 *   con cada toggle de chip).
 */

import { parseParams, serializeState } from './parse-params'
import type { FilterState } from './types'

/** Parsea el FilterState desde `window.location.search`. */
export function readUrl(): FilterState {
  return parseParams(new URLSearchParams(window.location.search))
}

/**
 * Actualiza la URL del navegador con el FilterState dado. Preserva pathname y
 * hash. Cuando el state esta vacio, deja la URL sin query string.
 */
export function syncUrl(state: FilterState): void {
  const query = serializeState(state)
  const { pathname, hash } = window.location
  const url =
    query === '' ? `${pathname}${hash}` : `${pathname}?${query}${hash}`
  window.history.replaceState(window.history.state, '', url)
}
