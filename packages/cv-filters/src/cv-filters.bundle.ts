/**
 * @module cv-filters/bundle
 * @description Entry point del bundle IIFE servido como `/cv-filters.js` en
 *   cada app. Se ejecuta una sola vez al cargar (script defer), se auto-
 *   monta sobre el DOM si encuentra `[data-filterable]`.
 *
 *   Flujo:
 *   1. Lee URL params (`readUrl()`).
 *   2. Llama `applyFilters()` con ese state inicial.
 *   3. Hace visible el filter shell (`[data-filter-bar]`).
 *   4. Pinta chips activos + badge contador segun el state.
 *   5. Cablea handlers:
 *      - `[data-filter-toggle]`: abre/cierra panel.
 *      - `[data-filter-chip]`: toggle valor en la dimension.
 *      - `[data-filter-clear="all"]`: reset.
 *      - Click en backdrop: cierra panel.
 *      - Escape key: cierra panel.
 *   6. Cada cambio: aplica filtros + actualiza URL + repaints chips + badge.
 *
 *   Sin frameworks, solo DOM APIs. Reentrante: puede correr en /about (con
 *   Astro view transitions) y en cv.html (standalone).
 */

import { applyFilters } from './apply-filters'
import { parseParams } from './parse-params'
import { syncUrl } from './sync-url'
import { emptyFilterState, type FilterState } from './types'

/** Toggle un valor en un array. Si esta presente lo quita, si no lo agrega. */
function toggleValue(arr: string[], value: string): string[] {
  return arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value]
}

/** Refleja el estado en los chips de UI. */
function paintChips(state: FilterState): void {
  const chips = document.querySelectorAll('[data-filter-chip]')
  for (const chip of chips) {
    const dim = chip.getAttribute('data-filter-chip') as keyof FilterState
    const value = chip.getAttribute('data-filter-value') ?? ''
    let isActive = false
    if (dim === 'hideConfidential') {
      isActive = state.hideConfidential
    } else if (dim === 'from' || dim === 'to') {
      isActive = (state[dim] as string) === value
    } else if (Array.isArray(state[dim])) {
      isActive = (state[dim] as string[]).includes(value)
    }
    chip.classList.toggle('is-active', isActive)
    chip.setAttribute('aria-pressed', isActive ? 'true' : 'false')
  }
}

/** Cuenta cuantos filtros activos hay en total. */
function countActiveFilters(state: FilterState): number {
  let count = 0
  count += state.tech.length
  count += state.seniority.length
  count += state.projectType.length
  count += state.skills.length
  if (state.from !== '') count += 1
  if (state.to !== '') count += 1
  if (state.hideConfidential) count += 1
  return count
}

/** Actualiza el badge contador en el toggle button. */
function paintBadge(state: FilterState): void {
  const badge = document.querySelector('[data-filter-count]')
  if (badge === null) return
  const count = countActiveFilters(state)
  if (count === 0) {
    badge.setAttribute('hidden', '')
    badge.textContent = '0'
  } else {
    badge.removeAttribute('hidden')
    badge.textContent = String(count)
  }
}

/** Toggle de un valor en el state dado, segun la dimension. */
function applyToggle(
  state: FilterState,
  dim: string,
  value: string,
): FilterState {
  const next: FilterState = { ...state }
  if (dim === 'tech') {
    next.tech = toggleValue(state.tech, value)
  } else if (dim === 'seniority') {
    next.seniority = toggleValue(state.seniority, value)
  } else if (dim === 'projectType') {
    next.projectType = toggleValue(state.projectType, value)
  } else if (dim === 'skills') {
    next.skills = toggleValue(state.skills, value)
  } else if (dim === 'from') {
    next.from = state.from === value ? '' : value
  } else if (dim === 'to') {
    next.to = state.to === value ? '' : value
  } else if (dim === 'hideConfidential') {
    next.hideConfidential = !state.hideConfidential
  }
  return next
}

/** Estado mutable global (encapsulado en closure del IIFE). */
let currentState: FilterState = emptyFilterState()

/** Re-aplica filtros + sincroniza URL + repinta chips + badge. */
function update(next: FilterState): void {
  currentState = next
  applyFilters(currentState)
  syncUrl(currentState)
  paintChips(currentState)
  paintBadge(currentState)
}

/** Abre o cierra el filter panel. */
function setPanelOpen(open: boolean): void {
  const shells = document.querySelectorAll('[data-filter-bar]')
  for (const shell of shells) {
    shell.classList.toggle('is-open', open)
    const panel = shell.querySelector('[data-filter-panel]')
    const backdrop = shell.querySelector('[data-filter-backdrop]')
    const toggle = shell.querySelector('[data-filter-toggle]')
    if (panel !== null) {
      if (open) {
        panel.removeAttribute('hidden')
      } else {
        panel.setAttribute('hidden', '')
      }
    }
    if (backdrop !== null) {
      if (open) {
        backdrop.removeAttribute('hidden')
      } else {
        backdrop.setAttribute('hidden', '')
      }
    }
    if (toggle !== null) {
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false')
    }
  }
}

function isPanelOpen(): boolean {
  const shell = document.querySelector('[data-filter-bar]')
  return shell?.classList.contains('is-open') ?? false
}

/** Wire-up de event listeners sobre chips, toggle, backdrop y clear-all. */
function bindHandlers(): void {
  document.addEventListener('click', (event) => {
    const target = event.target as Element | null
    if (target === null) {
      return
    }

    // Toggle / close panel
    const toggleEl = target.closest('[data-filter-toggle]')
    if (toggleEl !== null) {
      event.preventDefault()
      setPanelOpen(!isPanelOpen())
      return
    }

    // Chip click (toggle filter value)
    const chip = target.closest('[data-filter-chip]')
    if (chip !== null) {
      event.preventDefault()
      const dim = chip.getAttribute('data-filter-chip') ?? ''
      const value = chip.getAttribute('data-filter-value') ?? ''
      update(applyToggle(currentState, dim, value))
      return
    }

    // Clear all
    const clear = target.closest('[data-filter-clear="all"]')
    if (clear !== null) {
      event.preventDefault()
      update(emptyFilterState())
    }
  })

  // Cerrar panel con Escape
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isPanelOpen()) {
      setPanelOpen(false)
    }
  })
}

/** Revela el filter shell (oculto por default en SSR). */
function revealBar(): void {
  const bars = document.querySelectorAll('[data-filter-bar]')
  for (const bar of bars) {
    bar.removeAttribute('hidden')
  }
}

function init(): void {
  // No-op si no hay items filtrables en el DOM
  if (document.querySelector('[data-filterable]') === null) {
    return
  }
  currentState = parseParams(new URLSearchParams(window.location.search))
  applyFilters(currentState)
  paintChips(currentState)
  paintBadge(currentState)
  revealBar()
  bindHandlers()
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init, { once: true })
} else {
  init()
}
