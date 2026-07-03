/**
 * @module site-config (journey)
 * @description Config del sitio journey. Reusa el niche/curriculum `generic`
 *   (la experiencia 3D recorre el CV COMPLETO, no un niche). Los textos viven
 *   en los YAML i18n de `@portfolio/content` (`curriculum/generic.{es,en}.yaml`).
 */
import { defineSiteConfig } from '@portfolio/app-shared'
import { buildSiteUrl } from '@portfolio/app-shared/lib/site-urls'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'generic',
  siteUrl: import.meta.env.SITE_URL ?? buildSiteUrl('journey'),
})
