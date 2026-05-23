/**
 * @description Tests de scroll-depth: emite un evento `scroll_depth` por cada
 *   umbral cruzado (25/50/75/100 %), UNA sola vez cada uno [AC-8].
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  computeScrollPercent,
  initScrollDepth,
  SCROLL_THRESHOLDS,
} from '../../src/lib/scroll-depth'
import {
  configureTracking,
  resetTrackingConfig,
} from '../../src/lib/track-event'

/** Setea las metricas de scroll del documento y dispara un scroll event. */
function setScroll(opts: {
  scrollY: number
  scrollHeight: number
  innerHeight: number
}): void {
  Object.defineProperty(window, 'scrollY', {
    value: opts.scrollY,
    configurable: true,
    writable: true,
  })
  Object.defineProperty(window, 'innerHeight', {
    value: opts.innerHeight,
    configurable: true,
    writable: true,
  })
  Object.defineProperty(document.documentElement, 'scrollHeight', {
    value: opts.scrollHeight,
    configurable: true,
    writable: true,
  })
}

describe('scroll-depth', () => {
  beforeEach(() => {
    localStorage.clear()
    resetTrackingConfig()
    configureTracking({ apiEndpoint: 'https://api.test', niche: 'generic' })
    navigator.sendBeacon = vi.fn().mockReturnValue(true)
    // rAF sincrono para que evaluate() corra dentro del test.
    window.requestAnimationFrame = ((cb: FrameRequestCallback) => {
      cb(0)
      return 0
    }) as typeof window.requestAnimationFrame
  })

  afterEach(() => {
    localStorage.clear()
    resetTrackingConfig()
    vi.restoreAllMocks()
  })

  describe('computeScrollPercent', () => {
    it('Given a document without scroll When computeScrollPercent Then returns 100', () => {
      const pct = computeScrollPercent(
        { scrollY: 0, innerHeight: 800 } as Window,
        { scrollHeight: 800 } as HTMLElement,
      )
      expect(pct).toBe(100)
    })

    it('Given the page scrolled halfway When computeScrollPercent Then returns 50', () => {
      const pct = computeScrollPercent(
        { scrollY: 600, innerHeight: 800 } as Window,
        { scrollHeight: 2000 } as HTMLElement,
      )
      expect(pct).toBe(50)
    })

    it('Given scroll beyond the bottom When computeScrollPercent Then clamps to 100', () => {
      const pct = computeScrollPercent(
        { scrollY: 9999, innerHeight: 800 } as Window,
        { scrollHeight: 2000 } as HTMLElement,
      )
      expect(pct).toBe(100)
    })
  })

  describe('SCROLL_THRESHOLDS', () => {
    it('Given the threshold list When inspected Then it is exactly 25/50/75/100', () => {
      expect(SCROLL_THRESHOLDS).toEqual([25, 50, 75, 100])
    })
  })

  describe('initScrollDepth', () => {
    it('Given a long page at the top When init Then emits no scroll_depth event yet', () => {
      setScroll({ scrollY: 0, scrollHeight: 4000, innerHeight: 800 })
      const cleanup = initScrollDepth()
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
      cleanup()
    })

    it('Given a long page When scrolled to 50% Then emits scroll_depth once for 25 and once for 50', () => {
      setScroll({ scrollY: 0, scrollHeight: 4000, innerHeight: 800 })
      const cleanup = initScrollDepth()

      setScroll({ scrollY: 1600, scrollHeight: 4000, innerHeight: 800 })
      window.dispatchEvent(new Event('scroll'))

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(2)
      cleanup()
    })

    it('Given the 50% threshold already crossed When scrolling within it again Then does NOT re-emit [AC-8]', () => {
      setScroll({ scrollY: 0, scrollHeight: 4000, innerHeight: 800 })
      const cleanup = initScrollDepth()

      setScroll({ scrollY: 1600, scrollHeight: 4000, innerHeight: 800 })
      window.dispatchEvent(new Event('scroll'))
      // mismo punto: 25 y 50 ya disparados, no re-emite
      window.dispatchEvent(new Event('scroll'))

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(2)
      cleanup()
    })

    it('Given a full scroll to the bottom When dispatched Then emits exactly 4 scroll_depth events (one per threshold) [AC-8]', () => {
      setScroll({ scrollY: 0, scrollHeight: 4000, innerHeight: 800 })
      const cleanup = initScrollDepth()

      setScroll({ scrollY: 3200, scrollHeight: 4000, innerHeight: 800 })
      window.dispatchEvent(new Event('scroll'))

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(4)
      cleanup()
    })

    it('Given the bottom reached and another scroll event When dispatched Then no further events (all thresholds spent)', () => {
      setScroll({ scrollY: 0, scrollHeight: 4000, innerHeight: 800 })
      const cleanup = initScrollDepth()

      setScroll({ scrollY: 3200, scrollHeight: 4000, innerHeight: 800 })
      window.dispatchEvent(new Event('scroll'))
      window.dispatchEvent(new Event('scroll'))

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(4)
      cleanup()
    })

    it('Given a short page (no scrollbar) When init Then emits all 4 thresholds immediately (100%)', () => {
      setScroll({ scrollY: 0, scrollHeight: 700, innerHeight: 800 })
      const cleanup = initScrollDepth()
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(4)
      cleanup()
    })

    it('Given cleanup invoked When a scroll event fires Then no event is emitted (listener removed)', () => {
      setScroll({ scrollY: 0, scrollHeight: 4000, innerHeight: 800 })
      const cleanup = initScrollDepth()
      cleanup()

      setScroll({ scrollY: 3200, scrollHeight: 4000, innerHeight: 800 })
      window.dispatchEvent(new Event('scroll'))

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
    })
  })
})
