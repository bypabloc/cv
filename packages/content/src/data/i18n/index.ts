/**
 * @module i18n
 * @description Barrel del modulo i18n: textos de UI del portfolio (NO datos
 *   del CV). Tres familias:
 *
 *   - `elements`   -> labels reutilizables, identicos para las 6 apps
 *   - `curriculum` -> textos del CV especificos por app (meta, hero)
 *   - `hub-selector` -> textos del landing selector de la app hub
 *
 *   Cada familia carga sus YAML por idioma (es/en) y los valida con Zod.
 */

export {
  CURRICULUM_APPS,
  type CurriculumApp,
  getCurriculum,
} from './curriculum/index'
export { elements, getElements } from './elements/index'
export { getHubSelector, hubSelector } from './hub-selector/index'
