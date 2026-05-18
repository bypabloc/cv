/**
 * @module scroll-depth
 * @description Tracking de engagement por profundidad de scroll.
 *   `initScrollDepth()` emite un evento `scroll_depth` al cruzar cada umbral
 *   discreto (25/50/75/100 %), UNA sola vez por umbral. No es streaming
 *   continuo: acota el volumen de eventos.
 *
 *   Usa un scroll listener con throttle via `requestAnimationFrame` (el
 *   patron de `IntersectionObserver` de `reveal-on-scroll.ts` no aplica:
 *   no hay un elemento marcador por umbral, se mide el % del documento).
 *
 * @example
 *   import { initScrollDepth } from '@portfolio/ui/lib/scroll-depth'
 *   const cleanup = initScrollDepth()
 */
import { EVENT_TYPES } from '@portfolio/content/lib/event-types'
import { trackEvent } from './track-event'

/** Umbrales de profundidad (porcentaje del documento). */
export const SCROLL_THRESHOLDS: readonly number[] = [25, 50, 75, 100]

/**
 * @function computeScrollPercent
 * @description Calcula el porcentaje de scroll del documento (0-100). Si el
 *   documento no tiene scroll (cabe entero en el viewport) retorna 100.
 *
 * @param {Window} win - referencia a window
 * @param {HTMLElement} root - `document.documentElement`
 * @returns {number} porcentaje 0-100 (entero clampeado)
 */
export function computeScrollPercent(win: Window, root: HTMLElement): number {
  const scrollable = root.scrollHeight - win.innerHeight
  if (scrollable <= 0) return 100
  const ratio = win.scrollY / scrollable
  const pct = Math.round(ratio * 100)
  return Math.min(100, Math.max(0, pct))
}

/**
 * @function initScrollDepth
 * @description Registra el tracking de scroll depth. Cada umbral
 *   (25/50/75/100 %) emite `scroll_depth` una sola vez; cruzarlo de nuevo
 *   no re-emite. Si la pagina ya nace por encima de un umbral, lo emite al
 *   inicializar.
 *
 * @returns {() => void} cleanup que remueve el scroll listener
 */
export function initScrollDepth(): () => void {
  const win = globalThis.window
  const doc = globalThis.document
  if (!win || !doc?.documentElement) return () => undefined

  const root = doc.documentElement
  const fired = new Set<number>()
  let ticking = false

  const evaluate = (): void => {
    ticking = false
    const pct = computeScrollPercent(win, root)
    for (const threshold of SCROLL_THRESHOLDS) {
      if (pct >= threshold && !fired.has(threshold)) {
        fired.add(threshold)
        trackEvent(EVENT_TYPES.SCROLL_DEPTH, { depth: threshold })
      }
    }
  }

  const onScroll = (): void => {
    if (ticking) return
    ticking = true
    if (typeof win.requestAnimationFrame === 'function') {
      win.requestAnimationFrame(evaluate)
    } else {
      evaluate()
    }
  }

  // Evalua el estado inicial (paginas cortas cruzan umbrales al cargar).
  evaluate()
  win.addEventListener('scroll', onScroll, { passive: true })
  return () => win.removeEventListener('scroll', onScroll)
}
