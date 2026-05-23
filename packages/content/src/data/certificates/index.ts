/**
 * @module certificates
 * @description Certificaciones obtenidas. Origen: cache JSON generado por
 *   `scripts/fetch-cv-cache.mjs` (API GET /cv?action=certificates).
 */
import raw from '../../data-cache/certificates.json'
import { type Certificate, CertificateSchema } from '../../schemas'

const items: readonly Certificate[] = (raw as readonly unknown[]).map((entry) =>
  CertificateSchema.parse(entry),
)

export const certificates: readonly Certificate[] = [...items].sort((a, b) =>
  a.slug.localeCompare(b.slug),
)
