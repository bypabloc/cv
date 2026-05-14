/**
 * @module @portfolio/cv-filters
 * @description Public API del paquete. Exports listos para consumir desde el
 *   bundle IIFE (`cv-filters.bundle.ts`) o desde otros packages workspace.
 */

export { applyFilters } from './apply-filters'
export {
  buildStatsClient,
  type ClientStats,
  type ClientStatsInput,
  calcYearsFromStarts,
  countUniqueCompanies,
} from './build-stats-client'
export { matchesFilter } from './matches-filter'
export { parseParams, serializeState } from './parse-params'
export { type DateRange, rangesIntersect } from './ranges-intersect'
export { readUrl, syncUrl } from './sync-url'
export {
  type ApplyFiltersResult,
  emptyFilterState,
  FILTER_DIMENSIONS,
  type FilterDimension,
  type FilterState,
  type ItemAttrs,
  isEmptyState,
} from './types'
