/**
 * @module cv-filters/parse-params
 * @description Convierte URLSearchParams en FilterState. Sanitiza valores
 *   inválidos (los descarta silenciosamente). Inverso disponible via
 *   `serializeState`.
 *
 *   Vocabularios validos (deben mantenerse sincronizados con
 *   `@portfolio/content` schemas):
 *
 *   - seniority: 'intern' | 'junior' | 'mid' | 'senior' | 'lead'
 *   - projectType: 'web' | 'mobile' | 'cli' | 'library' | 'ai' | 'fintech-platform'
 *   - skills: 'technical' | 'soft'
 *
 *   `tech` queda libre (cualquier string). Si el usuario tipea ?tech=Foo y
 *   ningun item tiene tech=Foo, simplemente nada matchea (sin error).
 */

import { emptyFilterState, type FilterState, isEmptyState } from './types'

const VALID_SENIORITY = new Set(['intern', 'junior', 'mid', 'senior', 'lead'])

const VALID_PROJECT_TYPE = new Set([
  'web',
  'mobile',
  'cli',
  'library',
  'ai',
  'fintech-platform',
])

const VALID_SKILL_KIND = new Set(['technical', 'soft'])

/** Regex YYYY-MM con month 01-12. */
const YEAR_MONTH_RE = /^\d{4}-(0[1-9]|1[0-2])$/

/**
 * Parsea un valor CSV (`"a,b,c"`), trimea, descarta vacios, opcionalmente
 * filtra contra un set de valores validos.
 */
function parseCsv(value: string, validSet?: ReadonlySet<string>): string[] {
  const parts = value
    .split(',')
    .map((p) => p.trim())
    .filter((p) => p.length > 0)
  if (validSet === undefined) {
    return parts
  }
  return parts.filter((p) => validSet.has(p))
}

/**
 * Parsea una fecha YYYY-MM. Si invalida, retorna ''.
 */
function parseYearMonth(value: string): string {
  return YEAR_MONTH_RE.test(value) ? value : ''
}

/**
 * Parsea URLSearchParams en FilterState. Sanitiza inputs invalidos.
 *
 * Mapping URL -> state:
 *   ?tech=A,B          -> tech: ['A', 'B']
 *   ?seniority=senior  -> seniority: ['senior']
 *   ?type=web,ai       -> projectType: ['web', 'ai']  (nota: param 'type' por brevedad)
 *   ?skills=technical  -> skills: ['technical']
 *   ?from=2022-01      -> from: '2022-01'
 *   ?to=2026-05        -> to: '2026-05'
 *   ?hideConfidential=1 (o 'true') -> hideConfidential: true
 */
export function parseParams(params: URLSearchParams): FilterState {
  const state = emptyFilterState()

  const tech = params.get('tech')
  if (tech !== null) {
    state.tech = parseCsv(tech)
  }

  const seniority = params.get('seniority')
  if (seniority !== null) {
    state.seniority = parseCsv(seniority, VALID_SENIORITY)
  }

  const type = params.get('type')
  if (type !== null) {
    state.projectType = parseCsv(type, VALID_PROJECT_TYPE)
  }

  const skills = params.get('skills')
  if (skills !== null) {
    state.skills = parseCsv(skills, VALID_SKILL_KIND)
  }

  const from = params.get('from')
  if (from !== null) {
    state.from = parseYearMonth(from)
  }

  const to = params.get('to')
  if (to !== null) {
    state.to = parseYearMonth(to)
  }

  const hide = params.get('hideConfidential')
  if (hide !== null) {
    state.hideConfidential = hide === '1' || hide === 'true'
  }

  return state
}

/**
 * Serializa un FilterState a query string (sin el '?' inicial). Solo
 * incluye dimensiones activas. Inverso de `parseParams`: round-trip
 * preserva el state.
 *
 * @returns Query string sin '?' (ej. "tech=Vue&seniority=senior") o "" si
 *   el state esta vacio.
 */
export function serializeState(state: FilterState): string {
  if (isEmptyState(state)) {
    return ''
  }
  const params = new URLSearchParams()
  if (state.tech.length > 0) {
    params.set('tech', state.tech.join(','))
  }
  if (state.seniority.length > 0) {
    params.set('seniority', state.seniority.join(','))
  }
  if (state.projectType.length > 0) {
    params.set('type', state.projectType.join(','))
  }
  if (state.skills.length > 0) {
    params.set('skills', state.skills.join(','))
  }
  if (state.from !== '') {
    params.set('from', state.from)
  }
  if (state.to !== '') {
    params.set('to', state.to)
  }
  if (state.hideConfidential) {
    params.set('hideConfidential', '1')
  }
  return params.toString()
}
