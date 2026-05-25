/**
 * @module site-config (architect)
 * @description Config del sitio architect. Los textos viven en los YAML i18n
 *   de `@portfolio/content` (`curriculum/architect.{es,en}.yaml`).
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'architect',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
})
