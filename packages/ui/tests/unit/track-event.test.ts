/**
 * @description Tests de track-event: la API unica de emision de eventos.
 *   Verifica que `trackEvent` arma el payload con `event_id`/`session_id`/
 *   `event_type_id`/`event_props` y siempre emite (tracking always-on,
 *   sin gating de consentimiento).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buildTrackPayload,
  configureTracking,
  generateEventId,
  getSessionId,
  resetTrackingConfig,
  sendBeaconPayload,
  type TrackEventPayload,
  trackEvent,
} from '../../src/lib/track-event'

const PAGE_LOAD = '019e372b-e0a7-7154-8279-8829bcf6a08c'
const CTA_CLICK = '019e372b-e0a7-793b-84ed-690388a13b15'

/** Setea la query string que ve el modulo (location.search). */
function setSearch(search: string): void {
  Object.defineProperty(window, 'location', {
    value: { href: `https://x.test/${search}`, search, pathname: '/' },
    configurable: true,
    writable: true,
  })
}

describe('track-event', () => {
  beforeEach(() => {
    localStorage.clear()
    resetTrackingConfig()
    configureTracking({ apiEndpoint: 'https://api.test', niche: 'generic' })
    setSearch('')
    navigator.sendBeacon = vi.fn().mockReturnValue(true)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
    resetTrackingConfig()
  })

  describe('generateEventId', () => {
    it('Given crypto.randomUUID When generateEventId Then returns a 32-char hex string without dashes', () => {
      const id = generateEventId()
      expect(id).toMatch(/^[0-9a-f]{32}$/i)
    })

    it('Given two calls When generateEventId Then returns distinct ids', () => {
      expect(generateEventId()).not.toBe(generateEventId())
    })

    it('Given crypto.randomUUID unavailable When generateEventId Then uses the Date+random fallback', () => {
      const originalCrypto = globalThis.crypto
      // Simula un entorno sin crypto.randomUUID (rama de fallback).
      Object.defineProperty(globalThis, 'crypto', {
        configurable: true,
        writable: true,
        value: undefined,
      })

      const id = generateEventId()
      // El fallback NO es 32-hex: concatena base36 de Date.now() + 2 randoms.
      expect(id.length).toBeGreaterThan(0)
      expect(id).not.toMatch(/^[0-9a-f]{32}$/i)

      globalThis.crypto = originalCrypto
    })
  })

  describe('getSessionId', () => {
    it('Given empty localStorage When getSessionId Then creates and persists cf_session', () => {
      const sid = getSessionId()
      expect(localStorage.getItem('cf_session')).toBe(sid)
    })

    it('Given an existing cf_session When getSessionId Then returns the stored value', () => {
      const stored = 'abcdef0123456789abcdef0123456789'
      localStorage.setItem('cf_session', stored)
      expect(getSessionId()).toBe(stored)
    })

    it('Given localStorage.getItem throws When getSessionId Then returns a nostorage- fallback id', () => {
      vi.spyOn(localStorage, 'getItem').mockImplementation(() => {
        throw new Error('blocked')
      })
      expect(getSessionId()).toMatch(/^nostorage-[0-9a-f]+$/i)
    })
  })

  describe('sendBeaconPayload', () => {
    const payload: TrackEventPayload = {
      operation: 'tracking',
      action: 'track',
      session_id: 's',
      event_id: 'e',
      event_type_id: PAGE_LOAD,
      page_url: 'https://x.test/',
      page_path: '/',
      page_title: '',
      referrer: '',
      utm_source: '',
      utm_medium: '',
      utm_campaign: '',
      utm_content: '',
      viewport_width: 1280,
      viewport_height: 800,
      niche: 'generic',
    }

    it('Given no configured endpoint When sendBeaconPayload Then returns false without sending', () => {
      resetTrackingConfig()
      expect(sendBeaconPayload(payload)).toBe(false)
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
    })

    it('Given navigator.sendBeacon is unavailable When sendBeaconPayload Then falls back to fetch', () => {
      // @ts-expect-error: simulate a browser without sendBeacon
      navigator.sendBeacon = undefined
      const fetchMock = vi
        .fn()
        .mockResolvedValue(new Response(null, { status: 204 }))
      vi.stubGlobal('fetch', fetchMock)
      const result = sendBeaconPayload(payload)
      expect(result).toBe(true)
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })

    it('Given navigator.sendBeacon available When sendBeaconPayload Then uses beacon and returns its result', () => {
      const beacon = vi.fn().mockReturnValue(true)
      navigator.sendBeacon = beacon
      const fetchMock = vi.fn()
      vi.stubGlobal('fetch', fetchMock)

      const result = sendBeaconPayload(payload)

      expect(result).toBe(true)
      expect(beacon).toHaveBeenCalledTimes(1)
      // El beacon basto: NO se usa el fallback fetch.
      expect(fetchMock).toHaveBeenCalledTimes(0)
    })

    it('Given navigator.sendBeacon throws When sendBeaconPayload Then catches and falls back to fetch', () => {
      navigator.sendBeacon = vi.fn().mockImplementation(() => {
        throw new Error('beacon blew up')
      })
      const fetchMock = vi
        .fn()
        .mockResolvedValue(new Response(null, { status: 204 }))
      vi.stubGlobal('fetch', fetchMock)

      const result = sendBeaconPayload(payload)

      expect(result).toBe(true)
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })

    it('Given fetch throws synchronously When sendBeaconPayload Then returns false', () => {
      // @ts-expect-error: simulate a browser without sendBeacon
      navigator.sendBeacon = undefined
      vi.stubGlobal(
        'fetch',
        vi.fn().mockImplementation(() => {
          throw new Error('fetch unavailable')
        }),
      )

      expect(sendBeaconPayload(payload)).toBe(false)
    })
  })

  describe('buildTrackPayload', () => {
    it('Given an event type and props When buildTrackPayload Then includes core fields + page/utm/viewport (spec tracking-data-completeness)', () => {
      localStorage.setItem('cf_session', 'session000000000000000000000000')
      const payload = buildTrackPayload(CTA_CLICK, { href: '/contact' })
      expect(payload).toMatchObject({
        operation: 'tracking',
        action: 'track',
        session_id: 'session000000000000000000000000',
        event_type_id: CTA_CLICK,
        page_url: 'https://x.test/',
        page_path: '/',
        page_title: '',
        referrer: '',
        utm_source: '',
        utm_medium: '',
        utm_campaign: '',
        utm_content: '',
        niche: 'generic',
        event_props: { href: '/contact' },
      })
      // event_id es generado, solo verifica forma
      expect(payload.event_id).toMatch(/^[0-9a-f]{32}$/i)
      // viewport numeros (happy-dom default: 1024x768)
      expect(payload.viewport_width).toBeGreaterThan(0)
      expect(payload.viewport_height).toBeGreaterThan(0)
      expect(payload.device_pixel_ratio).toBeGreaterThan(0)
    })

    it('Given the event_id field When buildTrackPayload Then it is a 32-char hex string', () => {
      const payload = buildTrackPayload(PAGE_LOAD)
      expect(payload.event_id).toMatch(/^[0-9a-f]{32}$/i)
    })

    it('Given no props When buildTrackPayload Then omits event_props', () => {
      const payload = buildTrackPayload(PAGE_LOAD)
      expect(payload.event_props).toBe(undefined)
    })

    it('Given an empty props object When buildTrackPayload Then omits event_props', () => {
      const payload = buildTrackPayload(PAGE_LOAD, {})
      expect(payload.event_props).toBe(undefined)
    })

    it('Given URL with utm_source/medium When buildTrackPayload Then payload trae los 4 utm_* (vacio cuando no aplica) [AC-9]', () => {
      setSearch('?utm_source=linkedin&utm_medium=organic')
      const payload = buildTrackPayload(PAGE_LOAD)
      expect(payload.utm_source).toBe('linkedin')
      expect(payload.utm_medium).toBe('organic')
      expect(payload.utm_campaign).toBe('')
      expect(payload.utm_content).toBe('')
    })

    it('Given no query string When buildTrackPayload Then los 4 utm_* son string vacio (nunca undefined) [AC-9]', () => {
      setSearch('')
      const payload = buildTrackPayload(PAGE_LOAD)
      expect(payload.utm_source).toBe('')
      expect(payload.utm_medium).toBe('')
      expect(payload.utm_campaign).toBe('')
      expect(payload.utm_content).toBe('')
    })
  })

  describe('trackEvent (always-on)', () => {
    it('Given no previous localStorage state When trackEvent Then sends a beacon and returns true', () => {
      const result = trackEvent(CTA_CLICK, { href: '/contact' })
      expect(result).toBe(true)
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
    })

    it('Given no configured endpoint When trackEvent Then does NOT send and returns false', () => {
      resetTrackingConfig()
      const result = trackEvent(PAGE_LOAD)
      expect(result).toBe(false)
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
    })

    it('Given an event When trackEvent Then beacon URL is the configured endpoint + /track', () => {
      trackEvent(PAGE_LOAD)
      const [url] = vi.mocked(navigator.sendBeacon).mock.calls[0] ?? []
      expect(url).toBe('https://api.test/track')
    })

    it('Given an event with props When trackEvent Then the beacon body carries event_type_id and event_props', async () => {
      trackEvent(CTA_CLICK, { href: '/contact' })
      const [, blob] = vi.mocked(navigator.sendBeacon).mock.calls[0] ?? []
      const text = await (blob as Blob).text()
      const body = JSON.parse(text) as {
        event_type_id: string
        event_props: { href: string }
      }
      expect(body.event_type_id).toBe(CTA_CLICK)
      expect(body.event_props).toEqual({ href: '/contact' })
    })

    it('Given an event When trackEvent Then the beacon Blob is text/plain (CORS-safelisted, no preflight)', () => {
      trackEvent(PAGE_LOAD)
      const [, blob] = vi.mocked(navigator.sendBeacon).mock.calls[0] ?? []
      expect((blob as Blob).type).toBe('text/plain')
    })
  })
})
