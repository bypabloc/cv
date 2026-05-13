/**
 * @function initRevealOnScroll
 * @description Activa la clase `.is-visible` en cada `.reveal-on-scroll` cuando
 *   entra al viewport. Usa IntersectionObserver vanilla (cero deps).
 *
 *   Si prefers-reduced-motion: reduce esta activo, marca todos visibles
 *   inmediatamente y retorna noop.
 *
 * @returns funcion disconnect para limpiar el observer (opcional)
 *
 * @example
 *   // En BaseLayout.astro <script>:
 *   import { initRevealOnScroll } from '@portfolio/ui/lib/reveal-on-scroll'
 *   initRevealOnScroll()
 */
export function initRevealOnScroll(
  doc?: Document,
  win?: typeof window,
): () => void {
  const d = doc ?? globalThis.document
  const w = win ?? globalThis.window
  if (!d || !w) return () => undefined

  const targets = d.querySelectorAll<HTMLElement>('.reveal-on-scroll')
  if (targets.length === 0) return () => undefined

  const reducedMotion = w.matchMedia?.(
    '(prefers-reduced-motion: reduce)',
  ).matches
  if (reducedMotion || typeof IntersectionObserver === 'undefined') {
    for (const el of targets) el.classList.add('is-visible')
    return () => undefined
  }

  const observer = new IntersectionObserver(
    (entries, obs) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          obs.unobserve(entry.target)
        }
      }
    },
    { rootMargin: '0px 0px -10% 0px', threshold: 0.05 },
  )

  for (const el of targets) observer.observe(el)
  return () => observer.disconnect()
}
