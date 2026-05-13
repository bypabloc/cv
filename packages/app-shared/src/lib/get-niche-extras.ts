/**
 * @module get-niche-extras
 * @description Mapeo niche -> secciones extras renderizadas por CvSections.
 *   Permite que cada nicho tenga secciones unicas mas alla del Hero/Experience/
 *   Projects/Skills/Contact comunes.
 */
import type { Niche } from '@portfolio/content'

/** Secciones extras renderizadas por CvSections segun nicho. */
export type NicheExtra =
  | 'StatsBar'
  | 'SkillsMarquee'
  | 'AiWorkflowSection'
  | 'ArchitectureDiagram'
  | 'LeadershipStats'
  | 'AtsKeywordsPills'
  | 'AwardsHighlight'
  | 'EducationSection'

/**
 * Tabla niche -> extras. Orden importa (se renderiza en orden).
 */
const EXTRAS_BY_NICHE: Record<Niche, NicheExtra[]> = {
  generic: ['StatsBar', 'SkillsMarquee'],
  fintech: ['StatsBar', 'AtsKeywordsPills', 'SkillsMarquee'],
  architect: ['StatsBar', 'ArchitectureDiagram', 'SkillsMarquee'],
  leader: ['StatsBar', 'LeadershipStats', 'AwardsHighlight', 'SkillsMarquee'],
  vibe: ['StatsBar', 'AiWorkflowSection', 'SkillsMarquee'],
}

/**
 * @function getNicheExtras
 * @description Lista de secciones extras a renderizar para un nicho.
 *
 * @param {Niche} niche - Identificador del nicho
 * @returns {NicheExtra[]} Lista ordenada de extras
 *
 * @example
 *   getNicheExtras('vibe')
 *   // ['StatsBar', 'AiWorkflowSection', 'SkillsMarquee']
 */
export function getNicheExtras(niche: Niche): NicheExtra[] {
  return EXTRAS_BY_NICHE[niche]
}
