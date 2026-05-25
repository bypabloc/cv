/**
 * @module i18n/hub-selector
 * @description Carga los textos exclusivos del selector multi-niche de la
 *   app hub desde `hub-selector.<lang>.yaml`, validados por
 *   `HubSelectorStringsSchema`.
 *
 * @example
 *   import { getHubSelector } from '@portfolio/content'
 *   const t = getHubSelector('es')
 *   t.cardCta  // "Entrar"
 */
import { loadI18nFile } from '../../../lib/load-i18n-file'
import {
  type HubSelectorStrings,
  HubSelectorStringsSchema,
} from '../../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

const HUB_SELECTOR: Record<'es' | 'en', HubSelectorStrings> = {
  es: loadI18nFile('./hub-selector.es.yaml', modules, HubSelectorStringsSchema),
  en: loadI18nFile('./hub-selector.en.yaml', modules, HubSelectorStringsSchema),
}

/** Devuelve los textos del selector del hub para el locale dado. */
export function getHubSelector(locale: 'es' | 'en'): HubSelectorStrings {
  return HUB_SELECTOR[locale]
}

/** Mapa completo es/en (util para tests de paridad). */
export const hubSelector: Readonly<Record<'es' | 'en', HubSelectorStrings>> =
  HUB_SELECTOR
