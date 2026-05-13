/**
 * @module languages
 * @description Idiomas hablados + nivel. Data en YAML 1-por-idioma. El campo
 *   `slug` es opcional en el schema; las entries actuales no lo declaran (el
 *   filename solo aporta organizacion, no constraint).
 */
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Language, LanguageSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const languages: readonly Language[] = loadYamlEntries<Language>(
  modules,
  LanguageSchema,
)
