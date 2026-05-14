/**
 * @module cv-filters/types
 * @description Tipos publicos del filter engine. El engine es agnostico a la
 *   estructura del DOM, opera sobre data-* attrs en elementos marcados con
 *   `data-filterable`. Cada item declara sus dimensiones via data attrs:
 *
 *   - `data-tech="Vue,Astro,TypeScript"`         -> lista CSV
 *   - `data-seniority="senior"`                  -> valor unico
 *   - `data-project-type="web"`                  -> valor unico
 *   - `data-skill-kind="technical"`              -> 'technical' | 'soft'
 *   - `data-start="2024-01"`                     -> YYYY-MM (o vacio)
 *   - `data-end="2026-05"`                       -> YYYY-MM o vacio (=presente)
 *   - `data-confidential="true"`                 -> boolean string
 *
 *   Los chips de UI declaran sus targets via:
 *   - `data-filter-chip="tech"` + `data-filter-value="Vue"`
 *   - `data-filter-clear="all"`                  -> reset total
 */

/** Dimensiones soportadas por el filter engine. */
export const FILTER_DIMENSIONS = [
  'tech',
  'seniority',
  'projectType',
  'skills',
  'from',
  'to',
  'hideConfidential',
] as const

export type FilterDimension = (typeof FILTER_DIMENSIONS)[number]

/**
 * Estado declarativo de los filtros. Cada array es una lista de valores
 * permitidos (OR intra-dimension). Cuando esta vacio, la dimension no
 * restringe. AND inter-dimension.
 */
export interface FilterState {
  /** Tecnologias permitidas (CSV en URL: `?tech=Vue,Django`). OR intra. */
  tech: string[]
  /** Seniorities permitidos. OR intra. */
  seniority: string[]
  /** Project types permitidos. OR intra. */
  projectType: string[]
  /** Skill kinds permitidos: 'technical' | 'soft'. */
  skills: string[]
  /** Limite inferior del rango de fechas, YYYY-MM o ''. */
  from: string
  /** Limite superior del rango de fechas, YYYY-MM o ''. */
  to: string
  /** Si true, oculta items con data-confidential="true". */
  hideConfidential: boolean
}

/** Estado vacio (sin filtros, todo visible). */
export function emptyFilterState(): FilterState {
  return {
    tech: [],
    seniority: [],
    projectType: [],
    skills: [],
    from: '',
    to: '',
    hideConfidential: false,
  }
}

/** Verdadero si el state NO tiene ningun filtro activo. */
export function isEmptyState(state: FilterState): boolean {
  return (
    state.tech.length === 0 &&
    state.seniority.length === 0 &&
    state.projectType.length === 0 &&
    state.skills.length === 0 &&
    state.from === '' &&
    state.to === '' &&
    !state.hideConfidential
  )
}

/**
 * Snapshot de los data-* attrs de un item filtrable. Se construye al
 * recorrer el DOM en `apply-filters`. Lo expongo para que `matches-filter`
 * sea testeable sin DOM.
 */
export interface ItemAttrs {
  tech: string[]
  seniority: string
  projectType: string
  skillKind: string
  start: string
  end: string
  confidential: boolean
}

/** Resultado de aplicar filtros sobre el DOM. */
export interface ApplyFiltersResult {
  /** Cuantos items quedaron visibles por seccion. */
  visibleBySection: Record<string, number>
  /** Cuantos items totales quedaron visibles. */
  totalVisible: number
  /** Cuantos items totales habia. */
  totalAll: number
}
