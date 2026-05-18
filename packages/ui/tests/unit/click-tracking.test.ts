/**
 * @description Tests de click-tracking: el listener delegado en `document`
 *   resuelve el `data-track` del elemento clickeado o de un ancestro via
 *   `closest()`, lo mapea al UUID del catalogo y emite el evento [AC-3].
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buildClickProps,
  initClickTracking,
} from '../../src/lib/click-tracking'
import {
  configureTracking,
  resetTrackingConfig,
} from '../../src/lib/track-event'

const CTA_CLICK = '019e372b-e0a7-793b-84ed-690388a13b15'

describe('click-tracking', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    localStorage.clear()
    localStorage.setItem('cf_consent', 'accepted')
    resetTrackingConfig()
    configureTracking({ apiEndpoint: 'https://api.test', niche: 'generic' })
    navigator.sendBeacon = vi.fn().mockReturnValue(true)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    localStorage.clear()
    resetTrackingConfig()
    vi.restoreAllMocks()
  })

  describe('buildClickProps', () => {
    it('Given a plain element with data-track When buildClickProps Then props carry the code only', () => {
      const div = document.createElement('div')
      div.setAttribute('data-track', 'theme_toggle')
      expect(buildClickProps(div, 'theme_toggle')).toEqual({
        code: 'theme_toggle',
      })
    })

    it('Given an anchor with data-track When buildClickProps Then props carry code, href and text', () => {
      const a = document.createElement('a')
      a.href = 'https://x.test/contact'
      a.textContent = 'Contactar'
      a.setAttribute('data-track', 'cta_click')
      expect(buildClickProps(a, 'cta_click')).toEqual({
        code: 'cta_click',
        href: 'https://x.test/contact',
        text: 'Contactar',
      })
    })
  })

  describe('initClickTracking', () => {
    it('Given a document present When initClickTracking Then returns a function cleanup', () => {
      const cleanup = initClickTracking()
      expect(typeof cleanup).toBe('function')
      cleanup()
    })

    it('Given globalThis.document is undefined When initClickTracking Then returns a noop cleanup without throwing', () => {
      vi.stubGlobal('document', undefined)
      const cleanup = initClickTracking()
      expect(typeof cleanup).toBe('function')
      cleanup()
      vi.unstubAllGlobals()
    })

    it('Given a data-track element with an empty value When clicked Then sends nothing', () => {
      const el = document.createElement('button')
      el.setAttribute('data-track', '')
      document.body.appendChild(el)

      const cleanup = initClickTracking()
      el.click()

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
      cleanup()
    })

    it('Given an element with data-track When clicked Then sends a beacon with the resolved event_type_id', async () => {
      const a = document.createElement('a')
      a.href = 'https://x.test/contact'
      a.setAttribute('data-track', 'cta_click')
      document.body.appendChild(a)

      const cleanup = initClickTracking()
      a.click()

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
      const [, blob] = vi.mocked(navigator.sendBeacon).mock.calls[0] ?? []
      const body = JSON.parse(await (blob as Blob).text()) as {
        event_type_id: string
      }
      expect(body.event_type_id).toBe(CTA_CLICK)
      cleanup()
    })

    it('Given a child of a data-track ancestor When the child is clicked Then resolves the ancestor via closest()', () => {
      const a = document.createElement('a')
      a.href = 'https://x.test/contact'
      a.setAttribute('data-track', 'cta_click')
      const icon = document.createElement('span')
      a.appendChild(icon)
      document.body.appendChild(a)

      const cleanup = initClickTracking()
      icon.click()

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
      cleanup()
    })

    it('Given a click outside any data-track element When clicked Then sends nothing', () => {
      const plain = document.createElement('button')
      document.body.appendChild(plain)

      const cleanup = initClickTracking()
      plain.click()

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
      cleanup()
    })

    it('Given an unknown data-track code When clicked Then sends nothing (no UUID resolved)', () => {
      const el = document.createElement('button')
      el.setAttribute('data-track', 'not_a_real_event')
      document.body.appendChild(el)

      const cleanup = initClickTracking()
      el.click()

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
      cleanup()
    })

    it('Given cleanup was invoked When an element is clicked Then sends nothing (listener removed)', () => {
      const a = document.createElement('a')
      a.href = 'https://x.test/contact'
      a.setAttribute('data-track', 'cta_click')
      document.body.appendChild(a)

      const cleanup = initClickTracking()
      cleanup()
      a.click()

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
    })

    it('Given no consent When a data-track element is clicked Then sends nothing (gating) [AC-12]', () => {
      localStorage.removeItem('cf_consent')
      const a = document.createElement('a')
      a.href = 'https://x.test/contact'
      a.setAttribute('data-track', 'cta_click')
      document.body.appendChild(a)

      const cleanup = initClickTracking()
      a.click()

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
      cleanup()
    })
  })
})
