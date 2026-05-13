/**
 * @module number-counter
 * @description IntersectionObserver-based animated number counter.
 *   Cada elemento .stat-number con data-target="<number>" cuenta de 0 al
 *   target al entrar viewport (una sola vez).
 *
 *   En prefers-reduced-motion: reduce, escribe el target instantaneo.
 *   Bundle: ~0.9 KB minificado.
 *
 * @example
 *   <span class="stat-number" data-target="12">0</span>
 *   <script>initNumberCounters()</script>
 */

const ANIMATION_DURATION = 1400
const FRAME_MS = 16

function isReducedMotion(): boolean {
  if (typeof window === 'undefined') {
    return false
  }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function animateCounter(el: HTMLElement, target: number): void {
  const start = performance.now()

  const tick = (now: number): void => {
    const elapsed = now - start
    const progress = Math.min(elapsed / ANIMATION_DURATION, 1)
    // easeOutCubic
    const eased = 1 - (1 - progress) ** 3
    const current = Math.floor(eased * target)
    el.textContent = String(current)

    if (progress < 1) {
      requestAnimationFrame(tick)
    } else {
      el.textContent = String(target)
    }
  }

  requestAnimationFrame(tick)
}

/**
 * @function initNumberCounters
 * @description Activa animaciones de contador en todos los `.stat-number[data-target]`.
 *
 * @returns {() => void} Cleanup function para desconectar el observer
 *
 * @example
 *   const cleanup = initNumberCounters()
 */
export function initNumberCounters(): () => void {
  if (typeof window === 'undefined') {
    return () => {
      /* noop */
    }
  }

  const elements = Array.from(
    document.querySelectorAll<HTMLElement>('.stat-number[data-target]'),
  )

  if (elements.length === 0) {
    return () => {
      /* noop */
    }
  }

  if (isReducedMotion()) {
    for (const el of elements) {
      const target = Number(el.dataset.target ?? '0')
      el.textContent = String(target)
      el.dataset.counted = 'true'
    }
    return () => {
      /* noop */
    }
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        const el = entry.target as HTMLElement
        if (entry.isIntersecting && el.dataset.counted !== 'true') {
          const target = Number(el.dataset.target ?? '0')
          el.dataset.counted = 'true'
          if (Number.isInteger(target) && target > 0) {
            const intervalId = setInterval(() => {
              // bridge to RAF via timeout to keep imports light
              clearInterval(intervalId)
              animateCounter(el, target)
            }, FRAME_MS)
          }
        }
      }
    },
    { threshold: 0.4 },
  )

  for (const el of elements) {
    observer.observe(el)
  }

  return () => {
    observer.disconnect()
  }
}
