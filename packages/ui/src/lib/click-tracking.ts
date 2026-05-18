/**
 * @module click-tracking
 * @description Event delegation para tracking de clicks. `initClickTracking()`
 *   registra UN solo listener en `document`: cuando el usuario hace click,
 *   busca el `data-track="<code>"` mas cercano (el elemento o un ancestro via
 *   `closest()`), resuelve el `code` al UUID del catalogo `EVENT_TYPES` y
 *   emite el evento con `trackEvent`.
 *
 *   Event delegation (vs N listeners): funciona con contenido que aparece
 *   tras navegacion SPA — no hay que re-registrar nada en `astro:after-swap`.
 *
 * @example
 *   import { initClickTracking } from '@portfolio/ui/lib/click-tracking'
 *   const cleanup = initClickTracking()
 *   // en el HTML: <a data-track="cta_click" href="/contact">Contactar</a>
 */
import { eventTypeIdFromCode } from '@portfolio/content/lib/event-types'
import { trackEvent } from './track-event'

const TRACK_ATTR = 'data-track'
const TRACK_SELECTOR = '[data-track]'

/**
 * @function buildClickProps
 * @description Arma `event_props` con el contexto del elemento clickeado:
 *   `code`, y si es (o contiene) un ancla, el `href` y `text` del link.
 *
 * @param {Element} el - el elemento que lleva `data-track`
 * @param {string} code - el valor de `data-track`
 * @returns {Record<string, unknown>} props para `trackEvent`
 */
export function buildClickProps(
  el: Element,
  code: string,
): Record<string, unknown> {
  const props: Record<string, unknown> = { code }
  const anchor = el instanceof HTMLAnchorElement ? el : el.querySelector('a')
  if (anchor instanceof HTMLAnchorElement) {
    if (anchor.href) props.href = anchor.href.slice(0, 500)
    const text = anchor.textContent?.trim()
    if (text) props.text = text.slice(0, 120)
  }
  return props
}

/**
 * @function initClickTracking
 * @description Registra el listener delegado de clicks en `document`.
 *   Idempotente entre navegaciones SPA: el listener vive en `document`,
 *   que persiste a traves de los `astro:after-swap`.
 *
 * @returns {() => void} cleanup que remueve el listener
 */
export function initClickTracking(): () => void {
  const doc = globalThis.document
  if (!doc) return () => undefined

  const handler = (event: Event): void => {
    const target = event.target
    if (!(target instanceof Element)) return
    const tracked = target.closest(TRACK_SELECTOR)
    if (!tracked) return
    const code = tracked.getAttribute(TRACK_ATTR)
    if (!code) return
    const eventTypeId = eventTypeIdFromCode(code)
    if (!eventTypeId) return
    trackEvent(eventTypeId, buildClickProps(tracked, code))
  }

  doc.addEventListener('click', handler, { capture: true })
  return () => doc.removeEventListener('click', handler, { capture: true })
}
