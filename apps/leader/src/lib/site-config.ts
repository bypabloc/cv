/**
 * @module site-config (leader)
 * @description Config del sitio leader. Los textos viven en los YAML i18n
 *   de `@portfolio/content` (`curriculum/leader.{es,en}.yaml`).
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'leader',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
})
