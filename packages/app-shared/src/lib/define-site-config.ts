/**
 * @function defineSiteConfig
 * @description Factory que produce el config completo de un site del portfolio
 *   (NICHE + SITE_URL + OG_IMAGE + STRINGS).
 *
 *   Las strings ya NO se declaran inline: se cargan de los YAML i18n de
 *   `@portfolio/content` (`buildStrings(app)`). Cada app solo declara su
 *   `niche` — los textos especificos viven en `curriculum/<app>.<lang>.yaml`.
 *
 *   El siteUrl default cubre el caso comun (`https://<niche>.the-full-stack.com`).
 *   Las apps pueden pasarlo explicito si el dominio es distinto (ej. apex
 *   `the-full-stack.com` para generic).
 *
 * @example
 *   // apps/fintech/src/lib/site-config.ts
 *   import { defineSiteConfig } from '@portfolio/app-shared'
 *
 *   export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
 *     niche: 'fintech',
 *     siteUrl: import.meta.env.SITE_URL ?? undefined,
 *   })
 */
import type { CurriculumApp, Niche } from '@portfolio/content'
import { buildStrings, type I18nStrings } from './site-config'
import { buildSiteUrl, SITE_URLS } from './site-urls'

export interface DefineSiteConfigInput {
  /** Nicho del sitio. Ver `NICHES` en `@portfolio/content`. */
  niche: Niche
  /**
   * App del monorepo cuyo curriculum se carga. Por defecto coincide con el
   * niche; la app hub lo pasa explicito porque su niche es `generic` pero su
   * curriculum es `hub`.
   */
  app?: CurriculumApp
  /**
   * URL absoluta del sitio. Si se omite, se deriva de `https://<niche>.the-full-stack.com`.
   * Para sobrescribir en runtime usar `import.meta.env.SITE_URL` en el caller.
   */
  siteUrl?: string
  /**
   * Path del og-image relativo al SITE_URL. Default: `/og-image.svg`.
   */
  ogImagePath?: string
  /**
   * URL del hub para el item "Otras vistas" del nav. Si se omite, se usa
   * `SITE_URLS.hub`. La app hub debe pasar `null` para NO enlazarse a si misma.
   */
  hubHref?: string | null
}

export interface DefineSiteConfigOutput {
  NICHE: Niche
  SITE_URL: string
  OG_IMAGE: string
  STRINGS: Record<'es' | 'en', I18nStrings>
}

const DEFAULT_OG_PATH = '/og-image.svg'

/**
 * Deriva el SITE_URL default del niche cuando el caller no pasa `siteUrl`.
 *
 * Usa `buildSiteUrl` (env-driven via BASE_DOMAIN/SCHEME/PORT), de modo que
 * el default respeta el ambiente activo (prod / stage / dev / local) sin
 * hardcodear `the-full-stack.com`.
 */
function defaultSiteUrlFor(niche: Niche): string {
  return buildSiteUrl(niche)
}

export function defineSiteConfig(
  input: DefineSiteConfigInput,
): DefineSiteConfigOutput {
  const NICHE = input.niche
  const app: CurriculumApp = input.app ?? (NICHE as CurriculumApp)
  const SITE_URL = input.siteUrl ?? defaultSiteUrlFor(NICHE)
  const OG_IMAGE = `${SITE_URL}${input.ogImagePath ?? DEFAULT_OG_PATH}`
  // Auto-inject hubHref para que el navbar muestre "Otras vistas" -> hub.
  // `hubHref: null` desactiva el item (la app hub no se enlaza a si misma).
  const hubHref =
    input.hubHref === null ? undefined : (input.hubHref ?? SITE_URLS.hub)
  const STRINGS = buildStrings(app, hubHref)
  return { NICHE, SITE_URL, OG_IMAGE, STRINGS }
}
