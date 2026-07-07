/**
 * @module site-config (journey-realistic)
 * @description Config del sitio journey-realistic (banco de pruebas del
 *   plan docs/specs/journey-npc-realism, sin deploy). Reusa el
 *   niche/curriculum `generic` (la experiencia 3D recorre el CV COMPLETO,
 *   no un niche). Los textos viven en los YAML i18n de `@portfolio/content`
 *   (`curriculum/generic.{es,en}.yaml`). No usa `buildSiteUrl` (esa app NO
 *   se despliega, evita extender el tipo SiteKey compartido por esto).
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'generic',
  siteUrl: import.meta.env.SITE_URL ?? 'http://localhost:4328',
})
