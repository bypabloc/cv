/**
 * @function defineSiteConfig
 * @description Factory que produce el config completo de un site del portfolio
 *   (NICHE + SITE_URL + OG_IMAGE + STRINGS) a partir de los overrides especificos.
 *
 *   Cada app del monorepo (generic, fintech, architect, leader, vibe) declara
 *   los strings que la diferencian (meta titles, ATS keywords, etc.) en una
 *   sola llamada — sin necesidad de exportar manualmente `NICHE`, `SITE_URL`,
 *   `OG_IMAGE` y `STRINGS` por separado.
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
 *     overrides: {
 *       metaTitleEs: 'Pablo Contreras — Senior Fintech Engineer',
 *       metaTitleEn: 'Pablo Contreras — Senior Fintech Engineer',
 *       // ... resto de overrides
 *     },
 *   })
 */
import type { Niche } from '@portfolio/content'
import {
  buildStrings,
  type I18nStrings,
  type SiteOverrides,
} from './site-config'
import { buildSiteUrl, SITE_URLS } from './site-urls'

export interface DefineSiteConfigInput {
  /** Nicho del sitio. Ver `NICHES` en `@portfolio/content`. */
  niche: Niche
  /** Strings especificas del sitio (meta, hero, ATS). */
  overrides: SiteOverrides
  /**
   * URL absoluta del sitio. Si se omite, se deriva de `https://<niche>.the-full-stack.com`.
   * Para sobrescribir en runtime usar `import.meta.env.SITE_URL` en el caller.
   */
  siteUrl?: string
  /**
   * Path del og-image relativo al SITE_URL. Default: `/og-image.svg`.
   */
  ogImagePath?: string
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
 * hardcodear `the-full-stack.com`. En prod el niche `generic` mapea al apex
 * del dominio; en dev/stage al apex del env (`portfolio.{env}.the-full-stack.com`).
 */
function defaultSiteUrlFor(niche: Niche): string {
  return buildSiteUrl(niche)
}

export function defineSiteConfig(
  input: DefineSiteConfigInput,
): DefineSiteConfigOutput {
  const NICHE = input.niche
  const SITE_URL = input.siteUrl ?? defaultSiteUrlFor(NICHE)
  const OG_IMAGE = `${SITE_URL}${input.ogImagePath ?? DEFAULT_OG_PATH}`
  // Auto-inject hubHref para que el navbar muestre "Otras vistas" -> hub.
  // Solo se aplica si el caller no lo definio manualmente. Las 5 apps niche
  // se benefician sin tocar su site-config; el caller puede pasar
  // `hubHref: undefined` explicitamente para desactivarlo (ej. la app hub).
  const overridesWithHub: SiteOverrides = {
    ...input.overrides,
    hubHref:
      input.overrides.hubHref !== undefined
        ? input.overrides.hubHref
        : SITE_URLS.hub,
  }
  const STRINGS = buildStrings(overridesWithHub)
  return { NICHE, SITE_URL, OG_IMAGE, STRINGS }
}
