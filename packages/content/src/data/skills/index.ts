/**
 * @module skills
 * @description Categorias de skills agrupadas por dominio (technical/soft).
 *   Data en YAML 1-por-categoria (slug = filename).
 */
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type SkillCategory, SkillCategorySchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const skills: readonly SkillCategory[] = loadYamlEntries<SkillCategory>(
  modules,
  SkillCategorySchema,
)
