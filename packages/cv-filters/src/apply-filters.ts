/**
 * @module cv-filters/apply-filters
 * @description Aplica un FilterState al DOM:
 *
 *   1. Recorre los elementos `[data-filterable]`, lee sus data-* attrs,
 *      decide via `matchesFilter` si quedan visibles y aplica `hidden`.
 *   2. Cuenta visibles por seccion (`data-filter-section="..."`) y muestra
 *      mensajes empty cuando una seccion queda en 0.
 *   3. Recalcula stats (`[data-stat="years"]`, etc.) si hay un
 *      `[data-stats-host]` con experiences visibles.
 *
 *   El engine es agnostico a si esta corriendo en /about (Astro SSR) o en
 *   cv.html (standalone): mismo contrato DOM, mismo comportamiento.
 *
 *   Para evitar memory leaks, todos los listeners y mutations son
 *   sincronos. No hay observers, no hay subscripciones a stores.
 */

import { buildStatsClient } from './build-stats-client'
import { matchesFilter } from './matches-filter'
import type { ApplyFiltersResult, FilterState, ItemAttrs } from './types'

/** Convierte un valor CSV de data-* en array (vacio si '' o ausente). */
function csvAttr(el: Element, name: string): string[] {
  const raw = el.getAttribute(name) ?? ''
  return raw
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
}

/** Lee los data-* attrs de un item filtrable y los normaliza a ItemAttrs. */
function readItemAttrs(el: Element): ItemAttrs {
  return {
    tech: csvAttr(el, 'data-tech'),
    seniority: el.getAttribute('data-seniority') ?? '',
    projectType: el.getAttribute('data-project-type') ?? '',
    skillKind: el.getAttribute('data-skill-kind') ?? '',
    start: el.getAttribute('data-start') ?? '',
    end: el.getAttribute('data-end') ?? '',
    confidential: el.getAttribute('data-confidential') === 'true',
  }
}

/** Aplica `hidden` segun match. Mantiene el DOM como source-of-truth. */
function setHidden(el: Element, hidden: boolean): void {
  if (hidden) {
    el.setAttribute('hidden', '')
  } else {
    el.removeAttribute('hidden')
  }
}

/**
 * Aplica filtros al documento dado. Por default usa `document`. Inyectable
 * para tests con happy-dom.
 *
 * @returns Conteo de items visibles, agrupado por seccion + total global.
 */
export function applyFilters(
  state: FilterState,
  root: Document | Element = document,
): ApplyFiltersResult {
  const result: ApplyFiltersResult = {
    visibleBySection: {},
    totalVisible: 0,
    totalAll: 0,
  }

  const items = root.querySelectorAll('[data-filterable]')

  for (const el of items) {
    result.totalAll += 1

    const sectionEl = el.closest('[data-filter-section]')
    const section =
      sectionEl?.getAttribute('data-filter-section') ?? '__unknown__'

    const attrs = readItemAttrs(el)
    const matches = matchesFilter(attrs, state)

    setHidden(el, !matches)

    if (matches) {
      result.totalVisible += 1
      result.visibleBySection[section] =
        (result.visibleBySection[section] ?? 0) + 1
    } else if (!(section in result.visibleBySection)) {
      // Asegurar key presente con 0 si seccion existe.
      result.visibleBySection[section] = 0
    }
  }

  applyEmptyStates(root, result)
  recalcStats(root, state)

  return result
}

/**
 * Para cada `[data-filter-section]`: si tiene items y todos quedaron
 * ocultos, mostrar el `[data-filter-empty]` interno; si hay visibles,
 * ocultarlo.
 */
function applyEmptyStates(
  root: Document | Element,
  result: ApplyFiltersResult,
): void {
  const sections = root.querySelectorAll('[data-filter-section]')
  for (const section of sections) {
    const name = section.getAttribute('data-filter-section') ?? '__unknown__'
    const emptyEl = section.querySelector('[data-filter-empty]')
    if (emptyEl === null) {
      continue
    }
    const visible = result.visibleBySection[name] ?? 0
    setHidden(emptyEl, visible > 0)
  }
}

/**
 * Recalcula los stats numericos si hay un `[data-stats-host]` en el DOM.
 *
 * Estrategia: leer los experiences VISIBLES (data-filterable + data-section
 * "experience"), extraer starts y companies, y los certificates visibles.
 * Actualizar elementos `[data-stat="years"]`, `[data-stat="companies"]`,
 * `[data-stat="certifications"]`.
 *
 * `data-stat="countries"` queda igual (no se recalcula porque no hay info
 * estructurada de paises por experience).
 */
function recalcStats(root: Document | Element, _state: FilterState): void {
  const host = root.querySelector('[data-stats-host]')
  if (host === null) {
    return
  }

  // `data-filter-section` vive en el contenedor de seccion (no en el item).
  // Buscar items via descendant selector: section[data-filter-section] [data-filterable].
  const visibleExps = Array.from(
    root.querySelectorAll(
      '[data-filter-section="experience"] [data-filterable]:not([hidden])',
    ),
  )
  const visibleCerts = Array.from(
    root.querySelectorAll(
      '[data-filter-section="certificate"] [data-filterable]:not([hidden])',
    ),
  )

  const stats = buildStatsClient({
    experienceStarts: visibleExps
      .map((el) => el.getAttribute('data-start') ?? '')
      .filter((s) => s.length > 0),
    experienceCompanies: visibleExps
      .map((el) => el.getAttribute('data-company') ?? '')
      .filter((c) => c.length > 0),
    certificatesCount: visibleCerts.length,
  })

  const yearsEl = host.querySelector('[data-stat="years"]')
  if (yearsEl !== null) {
    yearsEl.textContent = String(stats.yearsExperience)
  }
  const companiesEl = host.querySelector('[data-stat="companies"]')
  if (companiesEl !== null) {
    companiesEl.textContent = String(stats.companies)
  }
  const certsEl = host.querySelector('[data-stat="certifications"]')
  if (certsEl !== null) {
    certsEl.textContent = String(stats.certifications)
  }
}
