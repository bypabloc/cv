/**
 * @module languages
 * @description Idiomas. Fuente: .claude/docs/cv/09-idiomas.md.
 */
import { type Language, LanguageSchema } from '../schemas'

const raw: Language[] = [
  {
    name: { es: 'Español', en: 'Spanish' },
    level: { es: 'Nativo', en: 'Native' },
  },
  {
    name: { es: 'Inglés', en: 'English' },
    level: {
      es: 'Intermedio en lectura, básico en escritura y habla',
      en: 'Intermediate reading, basic writing and speaking',
    },
  },
]

export const languages: Language[] = raw.map((l) => LanguageSchema.parse(l))
