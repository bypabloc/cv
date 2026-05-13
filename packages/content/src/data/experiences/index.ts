/**
 * @module experiences
 * @description 9 puestos laborales de Pablo Contreras (2013-presente).
 *   Data en archivos YAML 1-por-entry (slug-based filename). Este modulo
 *   solo orquesta: glob de los .yaml + validacion Zod + sort por slug.
 *
 * Para agregar/modificar un puesto: editar el `.yaml` correspondiente o
 * crear `<slug>.yaml` nuevo. El campo `slug` del YAML debe matchear el
 * filename (enforced por loadYamlEntries).
 */
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Experience, ExperienceSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const experiences: readonly Experience[] = loadYamlEntries<Experience>(
  modules,
  ExperienceSchema,
)
