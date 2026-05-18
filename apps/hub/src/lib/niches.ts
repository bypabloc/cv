/**
 * @module niches
 * @description Resuelve las 5 cards del hub selector combinando los textos
 *   i18n (`getHubSelector(locale)`) con los datos no-textuales (URL derivada
 *   de SITE_URLS, accent del DS). Los textos NO se hardcodean aqui.
 */
import { SITE_URLS } from '@portfolio/app-shared'
import { getHubSelector, type Niche } from '@portfolio/content'

export interface NicheCard {
  niche: Niche
  url: string
  title: string
  blurb: string
  accent: string
}

/** Accent del DS por niche. Dato visual, no textual. */
const ACCENT_BY_NICHE: Record<Niche, string> = {
  generic: '#9e9e99',
  fintech: '#4f6ef7',
  architect: '#38d9d6',
  leader: '#f4b740',
  vibe: '#f06e9c',
}

/**
 * Construye las cards del selector para un locale: el texto sale del YAML
 * i18n, la URL de SITE_URLS y el accent de ACCENT_BY_NICHE.
 */
export function getNicheCards(locale: 'es' | 'en'): NicheCard[] {
  return getHubSelector(locale).cards.map((card) => ({
    niche: card.niche,
    url: SITE_URLS[card.niche],
    title: card.title,
    blurb: card.blurb,
    accent: ACCENT_BY_NICHE[card.niche],
  }))
}
