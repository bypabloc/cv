/**
 * @module experiences
 * @description 9 puestos laborales de Pablo Contreras (2013-presente).
 *   Origen: cache JSON generado por `scripts/fetch-cv-cache.mjs` que pega
 *   al API GET /cv?action=experiences (Lambda cv -> Neon).
 *
 * Para agregar/modificar un puesto: hacerlo en la DB (Lambda db, command
 * seed) y regenerar el cache JSON. NO editar el cache a mano.
 */
import raw from '../../data-cache/experiences.json'
import { type Experience, ExperienceSchema } from '../../schemas'

const items: readonly Experience[] = (raw as readonly unknown[]).map((entry) =>
  ExperienceSchema.parse(entry),
)

// Ordenamiento estable por slug (igual que el patron loadYamlEntries).
export const experiences: readonly Experience[] = [...items].sort((a, b) =>
  a.slug.localeCompare(b.slug),
)
