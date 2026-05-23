/**
 * @module education
 * @description Formacion academica + autodidacta. Origen: cache JSON generado
 *   por `scripts/fetch-cv-cache.mjs` (API GET /cv?action=education).
 *
 *   `niches?` opcional en el schema: si se omite, la entry se renderiza en
 *   todos los niches (default actual). Cuando se define, habilita filtrado.
 */
import raw from '../../data-cache/education.json'
import { type Education, EducationSchema } from '../../schemas'

const items: readonly Education[] = (raw as readonly unknown[]).map((entry) =>
  EducationSchema.parse(entry),
)

export const education: readonly Education[] = [...items].sort((a, b) =>
  a.slug.localeCompare(b.slug),
)
