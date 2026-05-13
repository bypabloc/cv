/**
 * @module @portfolio/content
 * @description Barrel principal. Exporta schemas, types y todos los datos del CV.
 */

export { awards } from './data/awards'
export { certificates } from './data/certificates'
export { education } from './data/education'
export { experiences } from './data/experiences'
export { languages } from './data/languages'
export { profile } from './data/profile'
export { projects } from './data/projects'
export { publications } from './data/publications'
export { references } from './data/references'
export { skills } from './data/skills'
export { filterByNiche } from './lib/filter-by-niche'
export { formatRange, formatYearMonth } from './lib/format-date'
export { sortByPriority } from './lib/sort-by-priority'
export * from './schemas'
