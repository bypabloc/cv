/**
 * @module education
 * @description Formacion academica + autodidacta. Data en YAML 1-por-institucion
 *   (slug = filename). Schema en `../../schemas/EducationSchema`.
 *
 *   `niches?` opcional en el schema: si se omite, la entry se renderiza en
 *   todos los niches (default actual). Cuando se define, habilita filtrado.
 */
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Education, EducationSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const education: readonly Education[] = loadYamlEntries<Education>(
  modules,
  EducationSchema,
)
