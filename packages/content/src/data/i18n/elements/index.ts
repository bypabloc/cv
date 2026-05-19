/**
 * @module i18n/elements
 * @description Carga los labels reutilizables de UI (nav, stats, secciones,
 *   labels, componentes) desde `elements.<lang>.yaml`, validados por
 *   `ElementsStringsSchema`. Identicos para las 6 apps.
 *
 * @example
 *   import { getElements } from '@portfolio/content'
 *   const t = getElements('es')
 *   t.components.contactForm.submit  // "Enviar"
 */
import { loadI18nFile } from '../../../lib/load-i18n-file'
import { type ElementsStrings, ElementsStringsSchema } from '../../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

const ELEMENTS: Record<'es' | 'en', ElementsStrings> = {
  es: loadI18nFile('./elements.es.yaml', modules, ElementsStringsSchema),
  en: loadI18nFile('./elements.en.yaml', modules, ElementsStringsSchema),
}

/** Devuelve los labels de UI para el locale dado. */
export function getElements(locale: 'es' | 'en'): ElementsStrings {
  return ELEMENTS[locale]
}

/** Mapa completo es/en (util para tests de paridad). */
export const elements: Readonly<Record<'es' | 'en', ElementsStrings>> = ELEMENTS
