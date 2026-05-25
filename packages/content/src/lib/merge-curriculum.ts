/**
 * @function mergeCurriculum
 * @description Compone el curriculum final de una app: parte del `_base`
 *   (que declara TODAS las claves) y aplica el override parcial de la app
 *   por encima. Lo que el override no declara, cae al valor del `_base`.
 *
 *   El merge es shallow por rama (`meta`, `hero`, `sections`): cada rama se
 *   funde clave a clave. `atsKeywords` se reemplaza completo si el override
 *   lo declara (un array no se "mergea" parcialmente).
 *
 * @param base - Curriculum completo (`_base.<lang>.yaml`, valida el schema
 *   estricto `CurriculumStringsSchema`).
 * @param override - Override parcial de la app (`<app>.<lang>.yaml`, valida
 *   `CurriculumOverrideSchema`). Todas sus ramas son opcionales.
 *
 * @returns Curriculum completo de la app, listo para construir `STRINGS`.
 *
 * @example
 *   const vibe = mergeCurriculum(baseEs, vibeOverrideEs)
 *   vibe.hero.headline   // del override de vibe
 *   vibe.sections.skillsSubtitle  // del _base (vibe no lo override-a)
 */
import type { CurriculumOverride, CurriculumStrings } from '../schemas'

export function mergeCurriculum(
  base: CurriculumStrings,
  override: CurriculumOverride,
): CurriculumStrings {
  return {
    meta: { ...base.meta, ...override.meta },
    hero: { ...base.hero, ...override.hero },
    sections: { ...base.sections, ...override.sections },
    atsKeywords: override.atsKeywords ?? base.atsKeywords,
  }
}
