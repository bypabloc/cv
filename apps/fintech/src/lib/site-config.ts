/**
 * @module site-config (fintech)
 * @description Config del sitio fintech. Los textos viven en los YAML i18n
 *   de `@portfolio/content` (`curriculum/fintech.{es,en}.yaml`).
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'fintech',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
})
