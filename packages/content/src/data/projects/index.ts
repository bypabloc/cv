/**
 * @module projects
 * @description Side projects + case studies de Pablo Contreras. Data en YAML
 *   1-por-entry (slug = filename). Schema en `../../schemas/ProjectSchema`.
 *
 * Para agregar/modificar un proyecto: editar `<slug>.yaml` o crear uno nuevo.
 * `slug` del YAML debe matchear el filename (enforced por loadYamlEntries).
 */
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Project, ProjectSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const projects: readonly Project[] = loadYamlEntries<Project>(
  modules,
  ProjectSchema,
)
