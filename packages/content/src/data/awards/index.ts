/**
 * @module awards
 * @description Premios y reconocimientos. Data en YAML 1-por-award (slug =
 *   filename). Schema en `../../schemas/AwardSchema`.
 */

import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Award, AwardSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const awards: readonly Award[] = loadYamlEntries<Award>(
  modules,
  AwardSchema,
)
