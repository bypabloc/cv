/**
 * @module site-config (vibe)
 * @description Config del sitio vibe. Los textos viven en los YAML i18n
 *   de `@portfolio/content` (`curriculum/vibe.{es,en}.yaml`).
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'vibe',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
})
