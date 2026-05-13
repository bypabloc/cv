/**
 * @module @portfolio/content
 * @description Barrel principal. Exporta schemas, types y todos los datos del CV.
 */

export { awards } from './data/awards/index'
export { certificates } from './data/certificates/index'
export { education } from './data/education/index'
export { experiences } from './data/experiences/index'
export { languages } from './data/languages/index'
export { profile } from './data/profile'
export { projects } from './data/projects/index'
export { publications } from './data/publications/index'
export { references } from './data/references/index'
export { skills } from './data/skills/index'
export { filterByNiche } from './lib/filter-by-niche'
export { formatRange, formatYearMonth } from './lib/format-date'
export { sortByPriority } from './lib/sort-by-priority'
export * from './schemas'
