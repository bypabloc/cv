/**
 * @description Tests de track-event: la API unica de emision de eventos.
 *   Verifica que `trackEvent` arma el payload con `event_id`/`session_id`/
 *   `event_type_id`/`event_props` [AC-3], y que respeta el gating de
 *   consentimiento (`cf_consent`) y el bypass de QA `?cf_track=force`
 *   [AC-12].
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buildTrackPayload,
  configureTracking,
  generateEventId,
  getSessionId,
  hasTrackingConsent,
  isTrackingForced,
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
  })

  describe('isTrackingForced', () => {
    it('Given URL with ?cf_track=force When isTrackingForced Then returns true', () => {
      setSearch('?cf_track=force')
      expect(isTrackingForced()).toBe(true)
    })

    it('Given URL without the QA flag When isTrackingForced Then returns false', () => {
      setSearch('?utm_source=x')
      expect(isTrackingForced()).toBe(false)
    })
  })

  describe('hasTrackingConsent', () => {
    it('Given cf_consent=accepted When hasTrackingConsent Then returns true', () => {
      localStorage.setItem('cf_consent', 'accepted')
      expect(hasTrackingConsent()).toBe(true)
    })

    it('Given no cf_consent and no flag When hasTrackingConsent Then returns false', () => {
      expect(hasTrackingConsent()).toBe(false)
    })

    it('Given cf_consent=rejected When hasTrackingConsent Then returns false', () => {
      localStorage.setItem('cf_consent', 'rejected')
      expect(hasTrackingConsent()).toBe(false)
    })

    it('Given no consent but ?cf_track=force When hasTrackingConsent Then returns true', () => {
      setSearch('?cf_track=force')
      expect(hasTrackingConsent()).toBe(true)
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
      session_id: 's',
      event_id: 'e',
      event_type_id: PAGE_LOAD,
      page_url: 'https://x.test/',
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
  })

  describe('buildTrackPayload', () => {
    it('Given an event type and props When buildTrackPayload Then includes event_id, session_id, event_type_id and event_props', () => {
      localStorage.setItem('cf_session', 'session000000000000000000000000')
      const payload = buildTrackPayload(CTA_CLICK, { href: '/contact' })
      expect(payload).toEqual({
        session_id: 'session000000000000000000000000',
        event_id: payload.event_id,
        event_type_id: CTA_CLICK,
        page_url: 'https://x.test/',
        niche: 'generic',
        event_props: { href: '/contact' },
      })
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
  })

  describe('trackEvent gating', () => {
    it('Given no consent and no QA flag When trackEvent Then does NOT send and returns false [AC-12]', () => {
      const result = trackEvent(CTA_CLICK, { href: '/x' })
      expect(result).toBe(false)
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(0)
    })

    it('Given cf_consent=accepted When trackEvent Then sends a beacon to /track and returns true', () => {
      localStorage.setItem('cf_consent', 'accepted')
      const result = trackEvent(CTA_CLICK, { href: '/contact' })
      expect(result).toBe(true)
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
    })

    it('Given consent When trackEvent Then beacon URL is the configured endpoint + /track', () => {
      localStorage.setItem('cf_consent', 'accepted')
      trackEvent(PAGE_LOAD)
      const [url] = vi.mocked(navigator.sendBeacon).mock.calls[0] ?? []
      expect(url).toBe('https://api.test/track')
    })

    it('Given consent When trackEvent Then the beacon body carries event_type_id and event_props', async () => {
      localStorage.setItem('cf_consent', 'accepted')
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

    it('Given no consent but ?cf_track=force When trackEvent Then sends the beacon (QA bypass)', () => {
      setSearch('?cf_track=force')
      const result = trackEvent(PAGE_LOAD)
      expect(result).toBe(true)
      expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
    })
  })
})
