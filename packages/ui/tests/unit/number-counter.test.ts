/**
 * @description Tests para initNumberCounters. Verifica el comportamiento
 *   en prefers-reduced-motion (escribe target instantaneo) y en modo normal
 *   (IntersectionObserver dispara animacion via requestAnimationFrame).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { initNumberCounters } from '../../src/lib/number-counter'

describe('initNumberCounters', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false,
      media: '',
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }) as unknown as typeof window.matchMedia
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('Given DOM sin .stat-number When init Then retorna cleanup noop', () => {
    const cleanup = initNumberCounters()
    expect(typeof cleanup).toBe('function')
    cleanup()
  })

  it('Given prefers-reduced-motion: reduce When init Then escribe target instantaneo y marca counted', () => {
    window.matchMedia = vi.fn().mockReturnValue({
      matches: true,
      media: '(prefers-reduced-motion: reduce)',
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }) as unknown as typeof window.matchMedia
    const el = document.createElement('span')
    el.className = 'stat-number'
    el.dataset.target = '42'
    el.textContent = '0'
    document.body.appendChild(el)

    const cleanup = initNumberCounters()
    expect(el.textContent).toBe('42')
    expect(el.dataset.counted).toBe('true')
    cleanup()
  })

  it('Given .stat-number con data-target When init Then crea IntersectionObserver y observa el elemento', () => {
    const observeSpy = vi.fn()
    const disconnectSpy = vi.fn()
    class MockIO {
      observe = observeSpy
      disconnect = disconnectSpy
      unobserve = vi.fn()
      takeRecords = vi.fn().mockReturnValue([])
      root = null
      rootMargin = ''
      thresholds: number[] = []
    }
    vi.stubGlobal('IntersectionObserver', MockIO)

    const el = document.createElement('span')
    el.className = 'stat-number'
    el.dataset.target = '12'
    document.body.appendChild(el)

    const cleanup = initNumberCounters()
    expect(observeSpy).toHaveBeenCalledTimes(1)
    cleanup()
    expect(disconnectSpy).toHaveBeenCalledTimes(1)
  })

  it('Given .stat-number con data-target=0 When intersecting Then marca counted pero no dispara animateCounter', () => {
    let savedCallback:
      | ((entries: { isIntersecting: boolean; target: HTMLElement }[]) => void)
      | null = null
    class MockIO {
      constructor(
        cb: (
          entries: { isIntersecting: boolean; target: HTMLElement }[],
        ) => void,
      ) {
        savedCallback = cb
      }
      observe = vi.fn()
      disconnect = vi.fn()
      unobserve = vi.fn()
      takeRecords = vi.fn().mockReturnValue([])
      root = null
      rootMargin = ''
      thresholds: number[] = []
    }
    vi.stubGlobal('IntersectionObserver', MockIO)

    const el = document.createElement('span')
    el.className = 'stat-number'
    el.dataset.target = '0'
    document.body.appendChild(el)

    initNumberCounters()
    savedCallback?.([{ isIntersecting: true, target: el }])
    expect(el.dataset.counted).toBe('true')
  })

  it('Given IntersectionObserver callback con isIntersecting=false Then no marca counted', () => {
    let savedCallback:
      | ((entries: { isIntersecting: boolean; target: HTMLElement }[]) => void)
      | null = null
    class MockIO {
      constructor(
        cb: (
          entries: { isIntersecting: boolean; target: HTMLElement }[],
        ) => void,
      ) {
        savedCallback = cb
      }
      observe = vi.fn()
      disconnect = vi.fn()
      unobserve = vi.fn()
      takeRecords = vi.fn().mockReturnValue([])
      root = null
      rootMargin = ''
      thresholds: number[] = []
    }
    vi.stubGlobal('IntersectionObserver', MockIO)

    const el = document.createElement('span')
    el.className = 'stat-number'
    el.dataset.target = '10'
    document.body.appendChild(el)

    initNumberCounters()
    savedCallback?.([{ isIntersecting: false, target: el }])
    expect(el.dataset.counted).toBeUndefined()
  })

  it('Given IntersectionObserver callback con isIntersecting Then marca counted y dispara animacion', () => {
    let savedCallback:
      | ((entries: { isIntersecting: boolean; target: HTMLElement }[]) => void)
      | null = null
    class MockIO {
      constructor(
        cb: (
          entries: { isIntersecting: boolean; target: HTMLElement }[],
        ) => void,
      ) {
        savedCallback = cb
      }
      observe = vi.fn()
      disconnect = vi.fn()
      unobserve = vi.fn()
      takeRecords = vi.fn().mockReturnValue([])
      root = null
      rootMargin = ''
      thresholds: number[] = []
    }
    vi.stubGlobal('IntersectionObserver', MockIO)
    vi.useFakeTimers()

    const el = document.createElement('span')
    el.className = 'stat-number'
    el.dataset.target = '5'
    document.body.appendChild(el)

    initNumberCounters()
    expect(savedCallback).not.toBeNull()
    savedCallback?.([{ isIntersecting: true, target: el }])
    // setInterval(16) -> animateCounter via RAF
    vi.advanceTimersByTime(40)
    expect(el.dataset.counted).toBe('true')

    vi.useRealTimers()
  })
})
