/**
 * @module magnetic-cursor
 * @description Vanilla JS magnetic hover: elementos con clase `.magnetic`
 *   se mueven sutilmente hacia el cursor cuando esta cerca.
 *
 *   Desactivado en touch devices (hover: none) y prefers-reduced-motion.
 *   Bundle: ~1.4 KB minificado.
 *
 * @example
 *   import { initMagneticCursor } from '@portfolio/ui/lib/magnetic-cursor'
 *   initMagneticCursor()
 */

const MAX_DISTANCE = 60
const TRANSLATE_FACTOR = 0.25

function isInteractionAllowed(): boolean {
  if (typeof window === 'undefined') {
    return false
  }
  if (window.matchMedia('(hover: none)').matches) {
    return false
  }
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return false
  }
  return true
}

function attachMagnetic(el: HTMLElement): () => void {
  const handleMove = (event: MouseEvent): void => {
    const rect = el.getBoundingClientRect()
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    const dx = event.clientX - cx
    const dy = event.clientY - cy
    const distance = Math.hypot(dx, dy)

    if (distance > MAX_DISTANCE) {
      el.style.transform = 'translate3d(0, 0, 0)'
      return
    }

    const x = dx * TRANSLATE_FACTOR
    const y = dy * TRANSLATE_FACTOR
    el.style.transform = `translate3d(${x}px, ${y}px, 0)`
  }

  const handleLeave = (): void => {
    el.style.transform = 'translate3d(0, 0, 0)'
  }

  el.addEventListener('mousemove', handleMove)
  el.addEventListener('mouseleave', handleLeave)

  return () => {
    el.removeEventListener('mousemove', handleMove)
    el.removeEventListener('mouseleave', handleLeave)
  }
}

/**
 * @function initMagneticCursor
 * @description Activa el efecto magnetico en todos los `.magnetic` del DOM.
 *
 * @returns {() => void} Cleanup function para remover listeners
 *
 * @example
 *   const cleanup = initMagneticCursor()
 *   // Mas tarde:
 *   cleanup()
 */
export function initMagneticCursor(): () => void {
  if (!isInteractionAllowed()) {
    return () => {
      /* noop */
    }
  }

  const elements = Array.from(
    document.querySelectorAll<HTMLElement>('.magnetic'),
  )
  const cleanups = elements.map((el) => attachMagnetic(el))

  return () => {
    for (const cleanup of cleanups) {
      cleanup()
    }
  }
}
