/**
 * @module event-types
 * @description Catalogo de tipos de evento de tracking. Replica los UUID de la
 *   tabla SQL `event_types` (fuente de verdad: migration 006 + seed de
 *   SPEC-200). El cliente usa estas constantes en build-time, sin consultar la
 *   DB ni hacer requests extra.
 *
 *   Un test de paridad (event-types.test.ts) verifica que cada UUID de
 *   `EVENT_TYPES` coincide con el del seed SQL — cualquier divergencia falla.
 *
 * @example
 *   import { EVENT_TYPES } from '@portfolio/content'
 *   const payload = { event_type_id: EVENT_TYPES.PAGE_LOAD }
 */

/**
 * Mapa de tipos de evento -> UUID del catalogo `event_types`.
 *
 * `PAGE_LOAD` se sembro en migration 006 (Fase 1). El resto lo siembra
 * migration 008 (SPEC-200): navegacion, clicks, embudo de contacto y
 * engagement. Cada UUID es identico al del seed SQL — el test de paridad
 * `event-types.test.ts` falla ante cualquier divergencia.
 */
export const EVENT_TYPES = {
  // Navegacion
  PAGE_LOAD: '019e372b-e0a7-7154-8279-8829bcf6a08c',
  SPA_NAVIGATION: '019e372b-e0a7-70c6-8e56-2b643ddf1702',
  // Clicks
  CTA_CLICK: '019e372b-e0a7-793b-84ed-690388a13b15',
  NAV_CLICK: '019e372b-e0a7-776d-8598-81772857f6a8',
  PROJECT_LINK_CLICK: '019e372b-e0a7-7c1b-b8e7-3d822a5ce42d',
  EXPERIENCE_LINK_CLICK: '019e372b-e0a7-7267-8f09-f81f75d90f64',
  CV_DOWNLOAD: '019e372b-e0a7-78a3-ad27-15dfd3d266a2',
  THEME_TOGGLE: '019e372b-e0a7-767c-bbc4-d359c3522e86',
  EXTERNAL_LINK_CLICK: '019e372b-e0a7-7987-8699-8e6381865036',
  // Embudo de contacto
  CONTACT_VIEW: '019e372b-e0a7-7f8f-b568-3fbdb8a91756',
  CONTACT_FORM_START: '019e372b-e0a7-7467-a074-603b7e294cf8',
  CONTACT_FORM_SUBMIT: '019e372b-e0a7-7a02-b754-606a5fe38afc',
  CONTACT_FORM_SUCCESS: '019e372b-e0a7-7d1b-9bd3-3cb2ee92b4d7',
  CONTACT_FORM_ERROR: '019e372b-e0a7-77f6-897f-17f41a06b2c0',
  // Engagement
  SCROLL_DEPTH: '019e372b-e0a7-7067-a5c5-d0baf8352385',
  PAGE_EXIT: '019e372b-e0a7-78dd-a3b5-7cf649c4638f',
} as const

/**
 * @type EventTypeCode
 * @description Union de las claves validas de `EVENT_TYPES`.
 */
export type EventTypeCode = keyof typeof EVENT_TYPES

/**
 * @type EventTypeId
 * @description Union de los valores UUID validos de `EVENT_TYPES`.
 */
export type EventTypeId = (typeof EVENT_TYPES)[EventTypeCode]

/**
 * Mapa `code_name` (snake_case del catalogo SQL) -> UUID. Es el inverso del
 * naming SCREAMING_SNAKE_CASE de `EVENT_TYPES`: lo usa `click-tracking.ts`
 * para resolver el atributo `data-track="cta_click"` al UUID del evento.
 */
export const EVENT_TYPE_BY_CODE: Readonly<Record<string, string>> =
  Object.freeze(
    Object.fromEntries(
      Object.entries(EVENT_TYPES).map(([code, id]) => [code.toLowerCase(), id]),
    ),
  )

/**
 * @function eventTypeIdFromCode
 * @description Resuelve un `code_name` snake_case (ej. `nav_click`) al UUID
 *   del catalogo. Retorna `undefined` si el code no existe.
 *
 * @example
 *   eventTypeIdFromCode('nav_click')  // '019e372b-...'
 *   eventTypeIdFromCode('unknown')    // undefined
 */
export function eventTypeIdFromCode(code: string): string | undefined {
  return EVENT_TYPE_BY_CODE[code]
}
