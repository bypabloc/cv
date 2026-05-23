/**
 * @module languages
 * @description Idiomas hablados + nivel. Origen: cache JSON generado por
 *   `scripts/fetch-cv-cache.mjs` (API GET /cv?action=languages).
 */
import raw from '../../data-cache/languages.json'
import { type Language, LanguageSchema } from '../../schemas'

const items: readonly Language[] = (raw as readonly unknown[]).map((entry) =>
  LanguageSchema.parse(entry),
)

// Language tiene slug? opcional — fallback al primer campo estable.
export const languages: readonly Language[] = [...items].sort((a, b) =>
  (a.slug ?? '').localeCompare(b.slug ?? ''),
)
