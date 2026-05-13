/**
 * @description Tests para initMagneticCursor. Verifica que respeta hover:none
 *   y prefers-reduced-motion, y que adjunta listeners a .magnetic.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { initMagneticCursor } from '../../src/lib/magnetic-cursor'

describe('initMagneticCursor', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    // Default media-query: hover support + no reduced-motion
    window.matchMedia = vi.fn().mockImplementation((q: string) => ({
      matches: q === '(hover: hover)',
      media: q,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('Given touch device (hover: none) When init Then retorna noop sin error', () => {
    window.matchMedia = vi.fn().mockReturnValue({
      matches: true, // todo matchea (incluye hover:none)
      media: '',
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }) as unknown as typeof window.matchMedia
    const cleanup = initMagneticCursor()
    expect(typeof cleanup).toBe('function')
    cleanup()
  })

  it('Given prefers-reduced-motion: reduce When init Then retorna noop', () => {
    window.matchMedia = vi.fn().mockImplementation((q: string) => ({
      matches: q === '(prefers-reduced-motion: reduce)',
      media: q,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia
    const cleanup = initMagneticCursor()
    expect(typeof cleanup).toBe('function')
    cleanup()
  })

  it('Given hover support y no .magnetic en DOM When init Then retorna cleanup noop', () => {
    const cleanup = initMagneticCursor()
    expect(typeof cleanup).toBe('function')
    cleanup()
  })

  it('Given hover support y .magnetic en DOM When mousemove cerca Then aplica translate3d', () => {
    const btn = document.createElement('button')
    btn.className = 'magnetic'
    Object.defineProperty(btn, 'getBoundingClientRect', {
      value: () => ({
        left: 100,
        top: 100,
        width: 100,
        height: 40,
        right: 200,
        bottom: 140,
        x: 100,
        y: 100,
        toJSON: () => ({}),
      }),
    })
    document.body.appendChild(btn)
    initMagneticCursor()
    // cursor en (110, 110): cerca del centro (150, 120), distancia ~41px < 60
    btn.dispatchEvent(
      new MouseEvent('mousemove', { clientX: 110, clientY: 110 }),
    )
    expect(btn.style.transform).toMatch(/translate3d/u)
  })

  it('Given hover support y mousemove lejos Then resetea transform a (0,0,0)', () => {
    const btn = document.createElement('button')
    btn.className = 'magnetic'
    Object.defineProperty(btn, 'getBoundingClientRect', {
      value: () => ({
        left: 0,
        top: 0,
        width: 50,
        height: 20,
        right: 50,
        bottom: 20,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }),
    })
    document.body.appendChild(btn)
    initMagneticCursor()
    btn.dispatchEvent(
      new MouseEvent('mousemove', { clientX: 999, clientY: 999 }),
    )
    expect(btn.style.transform).toBe('translate3d(0, 0, 0)')
  })

  it('Given mouseleave Then resetea transform', () => {
    const btn = document.createElement('button')
    btn.className = 'magnetic'
    Object.defineProperty(btn, 'getBoundingClientRect', {
      value: () => ({
        left: 0,
        top: 0,
        width: 50,
        height: 20,
        right: 50,
        bottom: 20,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }),
    })
    document.body.appendChild(btn)
    initMagneticCursor()
    btn.style.transform = 'translate3d(5px, 5px, 0)'
    btn.dispatchEvent(new Event('mouseleave'))
    expect(btn.style.transform).toBe('translate3d(0, 0, 0)')
  })
})
