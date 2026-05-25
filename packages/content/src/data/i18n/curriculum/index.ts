/**
 * @module i18n/curriculum
 * @description Carga los textos del CV especificos por app (meta, hero,
 *   subtitulos de seccion, atsKeywords) desde `<app>.<lang>.yaml`, merge-ados
 *   sobre `_base.<lang>.yaml`.
 *
 *   `_base` declara todas las claves (valida `CurriculumStringsSchema`); cada
 *   app solo declara los overrides (valida `CurriculumOverrideSchema`). El
 *   merge rellena lo ausente con el valor del base.
 *
 * @example
 *   import { getCurriculum } from '@portfolio/content'
 *   const cv = getCurriculum('vibe', 'es')
 *   cv.hero.headline  // del override de vibe
 *   cv.sections.skillsSubtitle  // del _base (vibe no lo override-a)
 */
import { loadI18nFile } from '../../../lib/load-i18n-file'
import { mergeCurriculum } from '../../../lib/merge-curriculum'
import {
  CurriculumOverrideSchema,
  type CurriculumStrings,
  CurriculumStringsSchema,
} from '../../../schemas'

/** Apps del monorepo con curriculum propio. */
export const CURRICULUM_APPS = [
  'generic',
  'hub',
  'fintech',
  'architect',
  'leader',
  'vibe',
] as const
export type CurriculumApp = (typeof CURRICULUM_APPS)[number]

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

const base: Record<'es' | 'en', CurriculumStrings> = {
  es: loadI18nFile('./_base.es.yaml', modules, CurriculumStringsSchema),
  en: loadI18nFile('./_base.en.yaml', modules, CurriculumStringsSchema),
}

/** Memo de los curriculums ya compuestos (`<app>:<lang>`). */
const cache = new Map<string, CurriculumStrings>()

/**
 * Devuelve el curriculum completo de una app en un idioma: `_base` + el
 * override de la app. El resultado se memoiza por `<app>:<lang>`.
 */
export function getCurriculum(
  app: CurriculumApp,
  locale: 'es' | 'en',
): CurriculumStrings {
  const key = `${app}:${locale}`
  const hit = cache.get(key)
  if (hit) return hit
  const override = loadI18nFile(
    `./${app}.${locale}.yaml`,
    modules,
    CurriculumOverrideSchema,
  )
  const merged = mergeCurriculum(base[locale], override)
  cache.set(key, merged)
  return merged
}
