/**
 * @description Tests para initRevealOnScroll.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { initRevealOnScroll } from '../../src/lib/reveal-on-scroll'

describe('initRevealOnScroll', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('Given no targets When init Then returns noop', () => {
    const cleanup = initRevealOnScroll(document, window)
    expect(typeof cleanup).toBe('function')
    cleanup()
  })

  it('Given prefers-reduced-motion When init Then marks all visible immediately', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: true,
      media: '(prefers-reduced-motion: reduce)',
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    } as MediaQueryList)

    document.body.innerHTML = `
      <div class="reveal-on-scroll" id="a"></div>
      <div class="reveal-on-scroll" id="b"></div>
    `
    initRevealOnScroll(document, window)
    expect(
      document.querySelectorAll('.reveal-on-scroll.is-visible').length,
    ).toBe(2)
  })

  it('Given IntersectionObserver undefined When init Then marks all visible (fallback)', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: false,
      media: '(prefers-reduced-motion: reduce)',
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    } as MediaQueryList)

    const original = globalThis.IntersectionObserver
    // Simulate environment without IO without using `delete` (lint).
    Object.defineProperty(globalThis, 'IntersectionObserver', {
      configurable: true,
      writable: true,
      value: undefined,
    })

    document.body.innerHTML = '<div class="reveal-on-scroll"></div>'
    initRevealOnScroll(document, window)
    expect(
      document.querySelectorAll('.reveal-on-scroll.is-visible').length,
    ).toBe(1)

    globalThis.IntersectionObserver = original
  })

  it('Given IO available When init Then observes targets and returns cleanup', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: false,
      media: '(prefers-reduced-motion: reduce)',
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    } as MediaQueryList)

    const observed: Element[] = []
    const unobserved: Element[] = []
    let disconnected = false
    let cbRef: IntersectionObserverCallback | undefined

    const FakeIO = class {
      constructor(cb: IntersectionObserverCallback) {
        cbRef = cb
      }
      observe(el: Element) {
        observed.push(el)
      }
      unobserve(el: Element) {
        unobserved.push(el)
      }
      disconnect() {
        disconnected = true
      }
      takeRecords() {
        return []
      }
      root = null
      rootMargin = ''
      thresholds = []
    }
    globalThis.IntersectionObserver =
      FakeIO as unknown as typeof IntersectionObserver

    document.body.innerHTML = `
      <div class="reveal-on-scroll" id="a"></div>
      <div class="reveal-on-scroll" id="b"></div>
    `

    const cleanup = initRevealOnScroll(document, window)
    expect(observed.length).toBe(2)

    // Simulate the IO callback: a is intersecting, b is not.
    const targets = Array.from(
      document.querySelectorAll<HTMLElement>('.reveal-on-scroll'),
    )
    const entries = [
      {
        target: targets[0] as HTMLElement,
        isIntersecting: true,
        intersectionRatio: 1,
      },
      {
        target: targets[1] as HTMLElement,
        isIntersecting: false,
        intersectionRatio: 0,
      },
    ] as unknown as IntersectionObserverEntry[]
    cbRef?.(entries, {
      unobserve: (el: Element) => unobserved.push(el),
      observe: () => undefined,
      disconnect: () => undefined,
      takeRecords: () => [],
      root: null,
      rootMargin: '',
      thresholds: [],
    } as IntersectionObserver)

    expect(targets[0]?.classList.contains('is-visible')).toBe(true)
    expect(targets[1]?.classList.contains('is-visible')).toBe(false)
    expect(unobserved.length).toBe(1)

    cleanup()
    expect(disconnected).toBe(true)
  })

  it('Given no window When init Then returns noop', () => {
    const cleanup = initRevealOnScroll(
      document,
      undefined as unknown as typeof window,
    )
    expect(typeof cleanup).toBe('function')
  })
})
