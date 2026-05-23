/**
 * @module awards
 * @description Premios y reconocimientos. Origen: cache JSON generado
 *   por `scripts/fetch-cv-cache.mjs` (API GET /cv?action=awards).
 */
import raw from '../../data-cache/awards.json'
import { type Award, AwardSchema } from '../../schemas'

const items: readonly Award[] = (raw as readonly unknown[]).map((entry) =>
  AwardSchema.parse(entry),
)

export const awards: readonly Award[] = [...items].sort((a, b) =>
  a.slug.localeCompare(b.slug),
)
