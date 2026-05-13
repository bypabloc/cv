/**
 * @module publications
 * @description Articulos publicados (Medium, etc). Data en YAML 1-por-articulo
 *   (slug = filename). Schema en `../../schemas/PublicationSchema`.
 */
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Publication, PublicationSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const publications: readonly Publication[] =
  loadYamlEntries<Publication>(modules, PublicationSchema)
