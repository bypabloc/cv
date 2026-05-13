/**
 * @module certificates
 * @description Certificaciones obtenidas (cursos, programas). Data en YAML
 *   1-por-cert (slug = filename). Schema en `../../schemas/CertificateSchema`.
 */

import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Certificate, CertificateSchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const certificates: readonly Certificate[] =
  loadYamlEntries<Certificate>(modules, CertificateSchema)
