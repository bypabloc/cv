/**
 * @module site-config (generic)
 * @description Config del sitio generic. Los textos viven en los YAML i18n
 *   de `@portfolio/content` (`curriculum/generic.{es,en}.yaml`).
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'generic',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
})
