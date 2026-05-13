/**
 * @module references
 * @description Referencias profesionales. Data en YAML 1-por-referencia
 *   (slug = filename). Schema en `../../schemas/ReferenceSchema`.
 *
 *   `niches?` opcional: si se omite, la reference se renderiza en todos los
 *   niches (default actual).
 */
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Reference, ReferenceSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const references: readonly Reference[] = loadYamlEntries<Reference>(
  modules,
  ReferenceSchema,
)
