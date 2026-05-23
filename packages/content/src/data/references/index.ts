/**
 * @module references
 * @description Referencias profesionales. Origen: cache JSON generado por
 *   `scripts/fetch-cv-cache.mjs` (API GET /cv?action=references).
 *
 *   `niches?` opcional: si se omite, la reference se renderiza en todos los
 *   niches (default actual).
 */
import raw from '../../data-cache/references.json'
import { type Reference, ReferenceSchema } from '../../schemas'

const items: readonly Reference[] = (raw as readonly unknown[]).map((entry) =>
  ReferenceSchema.parse(entry),
)

export const references: readonly Reference[] = [...items].sort((a, b) =>
  a.slug.localeCompare(b.slug),
)
