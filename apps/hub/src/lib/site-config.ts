/**
 * @module site-config (hub)
 * @description Config del sitio hub (selector multi-niche). El hub no
 *   renderiza `CvSections`, pero sus paginas (index, contact) consumen
 *   `STRINGS` para meta, hero y los textos de componentes compartidos.
 *
 *   El niche tecnico es `generic` (para JSON-LD y tokens visuales); el
 *   curriculum es `hub` (`curriculum/hub.{es,en}.yaml`). `omitNicheDropdown:
 *   true` evita que el nav muestre el dropdown "Otras vistas" en el propio
 *   hub (donde no aplica).
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'generic',
  app: 'hub',
  omitNicheDropdown: true,
  siteUrl: import.meta.env.SITE_URL ?? undefined,
})
