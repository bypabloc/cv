/**
 * @module site-config (journey)
 * @description Config del sitio journey. Reusa el niche/curriculum `generic`
 *   (la experiencia 3D recorre el CV COMPLETO, no un niche). Los textos viven
 *   en los YAML i18n de `@portfolio/content` (`curriculum/generic.{es,en}.yaml`).
 *
 *   `journey` aun no es un SiteKey de `site-urls` (la app no se deploya en
 *   este PR): el hostname se deriva del patron de los niches
 *   (`journey.<BASE_DOMAIN>`). El PR de deploy agrega 'journey' a SiteKey y
 *   elimina este workaround.
 */
import { defineSiteConfig } from '@portfolio/app-shared'
import { buildSiteUrl } from '@portfolio/app-shared/lib/site-urls'

function journeySiteUrl(): string {
  return buildSiteUrl('fintech').replace('//fintech.', '//journey.')
}

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'generic',
  siteUrl: import.meta.env.SITE_URL ?? journeySiteUrl(),
})
