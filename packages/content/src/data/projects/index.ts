/**
 * @module projects
 * @description Side projects + case studies de Pablo Contreras.
 *   Origen: cache JSON generado por `scripts/fetch-cv-cache.mjs`.
 */
import raw from '../../data-cache/projects.json'
import { type Project, ProjectSchema } from '../../schemas'

const items: readonly Project[] = (raw as readonly unknown[]).map((entry) =>
  ProjectSchema.parse(entry),
)

export const projects: readonly Project[] = [...items].sort((a, b) =>
  a.slug.localeCompare(b.slug),
)
