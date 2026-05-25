/**
 * @module stagger
 * @description Stagger fade-in para listas (experiences, projects,
 *   skills). Cada item recibe `--stagger-idx` (0..N) y la clase
 *   `stagger-pending`; al entrar al viewport se le agrega
 *   `stagger-visible` y la animacion CSS (definida en
 *   view-transitions.css) corre con `animation-delay: idx * 40ms`.
 *
 *   IntersectionObserver con `once: true` (unobserve tras el primer
 *   trigger). En navegacion via ClientRouter, cuando la pagina nueva
 *   monta la lista por primera vez, vuelve a observarse — solo NO
 *   reanima cuando ya esta visible.
 *
 *   prefers-reduced-motion: el CSS hace .stagger-pending {opacity:1}
 *   directo; este modulo sigue ejecutando pero el visual es instantaneo.
 *
 * @example
 *   import { applyStagger } from '@portfolio/ui/lib/stagger'
 *   document.addEventListener('astro:page-load', () => {
 *     document.querySelectorAll<HTMLElement>('[data-stagger]').forEach((el) => {
 *       applyStagger(el, ':scope > article')
 *     })
 *   })
 */

/**
 * @function applyStagger
 * @description Aplica el efecto stagger a los items hijos del container.
 *
 * @param {Element} container - elemento padre que contiene los items
 * @param {string} itemSelector - selector relativo (ej. `:scope > article`)
 * @param {number} [delayMs=40] - delay entre items en ms (no usado por
 *   la animacion CSS — sirve de documentacion; el CSS lo deriva via
 *   `calc(var(--stagger-idx) * 40ms)`)
 * @returns {IntersectionObserver | null} observer activo (caller puede
 *   `disconnect()` cuando la pagina cambia) o null si IntersectionObserver
 *   no esta disponible (SSR/jsdom sin polyfill).
 */
export function applyStagger(
  container: Element,
  itemSelector: string,
  delayMs = 40,
): IntersectionObserver | null {
  const items = container.querySelectorAll<HTMLElement>(itemSelector)
  items.forEach((item, idx) => {
    item.style.setProperty('--stagger-idx', String(idx))
    item.classList.add('stagger-pending')
  })

  if (typeof IntersectionObserver === 'undefined') {
    // Fallback: aplicar todos visibles sin animacion
    items.forEach((item) => {
      item.classList.remove('stagger-pending')
      item.classList.add('stagger-visible')
    })
    return null
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('stagger-visible')
          observer.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.1 },
  )

  items.forEach((item) => {
    observer.observe(item)
  })
  // delayMs se conserva en la firma para futuro (override del 40ms del CSS).
  void delayMs
  return observer
}

/**
 * @function bindStaggerOnLoad
 * @description Helper conveniente: escanea `[data-stagger]` y aplica
 *   `applyStagger` a cada uno con `:scope > *` como selector default.
 *   Se invoca desde el script inline de cada pagina con stagger.
 *
 * @param {string} [itemSelector=':scope > *'] - selector relativo de items
 * @returns {IntersectionObserver[]} observers creados (uno por container)
 */
export function bindStaggerOnLoad(
  itemSelector = ':scope > *',
): IntersectionObserver[] {
  const containers = document.querySelectorAll<HTMLElement>('[data-stagger]')
  const observers: IntersectionObserver[] = []
  containers.forEach((c) => {
    const obs = applyStagger(c, itemSelector)
    if (obs) observers.push(obs)
  })
  return observers
}
