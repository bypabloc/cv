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
 * Fase 1 expone solo `PAGE_LOAD`. SPEC-200 amplia con clicks, embudo de
 * contacto y engagement (mismos UUID del seed SQL).
 */
export const EVENT_TYPES = {
  PAGE_LOAD: '019e372b-e0a7-7154-8279-8829bcf6a08c',
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
