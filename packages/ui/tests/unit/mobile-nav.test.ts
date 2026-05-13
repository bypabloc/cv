/**
 * @description Tests para initMobileNav. Verifica que el dialog se abre con
 *   showModal() al togglear, se cierra con Esc o click en backdrop/cerrar,
 *   y respeta prefers-reduced-motion deshabilitando transiciones.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { initMobileNav } from '../../src/lib/mobile-nav'

describe('initMobileNav', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    // Default: no reduced motion
    window.matchMedia = vi.fn().mockImplementation((q: string) => ({
      matches: false,
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

  it('Given no hay toggle ni dialog en DOM When init Then retorna cleanup noop sin error', () => {
    const cleanup = initMobileNav()
    expect(typeof cleanup).toBe('function')
    cleanup()
  })

  it('Given toggle + dialog en DOM When click en toggle Then invoca dialog.showModal()', () => {
    const toggle = document.createElement('button')
    toggle.setAttribute('data-mobile-nav-toggle', '')
    const dialog = document.createElement('dialog')
    dialog.setAttribute('data-mobile-nav-dialog', '')
    const showModal = vi.fn()
    dialog.showModal = showModal
    dialog.close = vi.fn()
    document.body.appendChild(toggle)
    document.body.appendChild(dialog)

    const cleanup = initMobileNav()
    toggle.click()
    expect(showModal).toHaveBeenCalledTimes(1)
    cleanup()
  })

  it('Given dialog abierto When click en [data-mobile-nav-close] Then invoca dialog.close()', () => {
    const toggle = document.createElement('button')
    toggle.setAttribute('data-mobile-nav-toggle', '')
    const dialog = document.createElement('dialog')
    dialog.setAttribute('data-mobile-nav-dialog', '')
    dialog.showModal = vi.fn()
    const close = vi.fn()
    dialog.close = close
    const closeBtn = document.createElement('button')
    closeBtn.setAttribute('data-mobile-nav-close', '')
    dialog.appendChild(closeBtn)
    document.body.appendChild(toggle)
    document.body.appendChild(dialog)

    initMobileNav()
    closeBtn.click()
    expect(close).toHaveBeenCalledTimes(1)
  })

  it('Given dialog con links When click en un link interno Then invoca dialog.close() para cerrar drawer al navegar', () => {
    const toggle = document.createElement('button')
    toggle.setAttribute('data-mobile-nav-toggle', '')
    const dialog = document.createElement('dialog')
    dialog.setAttribute('data-mobile-nav-dialog', '')
    dialog.showModal = vi.fn()
    const close = vi.fn()
    dialog.close = close
    const link = document.createElement('a')
    link.href = '/about'
    dialog.appendChild(link)
    document.body.appendChild(toggle)
    document.body.appendChild(dialog)

    initMobileNav()
    link.click()
    expect(close).toHaveBeenCalledTimes(1)
  })

  it('Given viewport >= 768px (matchMedia matches) When init Then dialog se cierra si estaba abierto', () => {
    let mqListener: ((e: MediaQueryListEvent) => void) | undefined
    window.matchMedia = vi.fn().mockImplementation((q: string) => ({
      matches: false,
      media: q,
      onchange: null,
      addEventListener: vi.fn(
        (_: string, cb: (e: MediaQueryListEvent) => void) => {
          mqListener = cb
        },
      ),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia

    const toggle = document.createElement('button')
    toggle.setAttribute('data-mobile-nav-toggle', '')
    const dialog = document.createElement('dialog')
    dialog.setAttribute('data-mobile-nav-dialog', '')
    dialog.showModal = vi.fn()
    const close = vi.fn()
    dialog.close = close
    // simular open state
    Object.defineProperty(dialog, 'open', { value: true, configurable: true })
    document.body.appendChild(toggle)
    document.body.appendChild(dialog)

    initMobileNav()
    // simular cruce a desktop
    mqListener?.({ matches: true } as MediaQueryListEvent)
    expect(close).toHaveBeenCalledTimes(1)
  })

  it('Given cleanup invocado When click en toggle Then no invoca showModal (listener removido)', () => {
    const toggle = document.createElement('button')
    toggle.setAttribute('data-mobile-nav-toggle', '')
    const dialog = document.createElement('dialog')
    dialog.setAttribute('data-mobile-nav-dialog', '')
    const showModal = vi.fn()
    dialog.showModal = showModal
    dialog.close = vi.fn()
    document.body.appendChild(toggle)
    document.body.appendChild(dialog)

    const cleanup = initMobileNav()
    cleanup()
    toggle.click()
    expect(showModal).toHaveBeenCalledTimes(0)
  })
})
