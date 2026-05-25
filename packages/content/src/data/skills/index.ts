/**
 * @module skills
 * @description Categorias de skills agrupadas por dominio (technical/soft).
 *   Origen: cache JSON generado por `scripts/fetch-cv-cache.mjs`
 *   (API GET /cv?action=skills).
 */
import raw from '../../data-cache/skills.json'
import { type SkillCategory, SkillCategorySchema } from '../../schemas'

const items: readonly SkillCategory[] = (raw as readonly unknown[]).map(
  (entry) => SkillCategorySchema.parse(entry),
)

export const skills: readonly SkillCategory[] = [...items].sort((a, b) =>
  a.slug.localeCompare(b.slug),
)
