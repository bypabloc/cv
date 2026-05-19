/**
 * @description Tests para cookie-consent (logica del CookieBanner GDPR).
 *   Cubre AC-2, AC-3, AC-6 (gating). Usa happy-dom. Los textos del banner
 *   ya no viven aqui (estan en el YAML i18n) — su test es de paridad.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  CONSENT_CHANGED_EVENT,
  isConsentValue,
  REOPEN_BANNER_EVENT,
  readConsent,
  STORAGE_KEY,
  writeConsent,
} from '../../src/lib/cookie-consent'

class MemoryStorage implements Storage {
  private store = new Map<string, string>()
  get length() {
    return this.store.size
  }
  clear() {
    this.store.clear()
  }
  getItem(key: string) {
    return this.store.get(key) ?? null
  }
  key(index: number) {
    return Array.from(this.store.keys())[index] ?? null
  }
  removeItem(key: string) {
    this.store.delete(key)
  }
  setItem(key: string, value: string) {
    this.store.set(key, value)
  }
}

const throwingStorage: Storage = {
  length: 0,
  clear: () => undefined,
  getItem: () => {
    throw new Error('storage disabled')
  },
  key: () => null,
  removeItem: () => undefined,
  setItem: () => {
    throw new Error('storage disabled')
  },
}

describe('constants', () => {
  it('Given the module When read STORAGE_KEY Then it is "cf_consent"', () => {
    expect(STORAGE_KEY).toBe('cf_consent')
  })

  it('Given the module When read event names Then they are namespaced', () => {
    expect(CONSENT_CHANGED_EVENT).toBe('portfolio:consent-changed')
    expect(REOPEN_BANNER_EVENT).toBe('portfolio:consent-reopen')
  })
})

describe('isConsentValue', () => {
  it('Given "accepted" or "rejected" When check Then returns true', () => {
    expect(isConsentValue('accepted')).toBe(true)
    expect(isConsentValue('rejected')).toBe(true)
  })

  it('Given an invalid value When check Then returns false', () => {
    expect(isConsentValue('maybe')).toBe(false)
    expect(isConsentValue(null)).toBe(false)
    expect(isConsentValue(undefined)).toBe(false)
    expect(isConsentValue(1)).toBe(false)
  })
})

describe('readConsent', () => {
  it('Given empty storage When read Then returns null', () => {
    const s = new MemoryStorage()
    expect(readConsent(s)).toBe(null)
  })

  it('Given stored "accepted" When read Then returns "accepted"', () => {
    const s = new MemoryStorage()
    s.setItem(STORAGE_KEY, 'accepted')
    expect(readConsent(s)).toBe('accepted')
  })

  it('Given stored "rejected" When read Then returns "rejected"', () => {
    const s = new MemoryStorage()
    s.setItem(STORAGE_KEY, 'rejected')
    expect(readConsent(s)).toBe('rejected')
  })

  it('Given stored garbage When read Then returns null', () => {
    const s = new MemoryStorage()
    s.setItem(STORAGE_KEY, 'banana')
    expect(readConsent(s)).toBe(null)
  })

  it('Given storage that throws When read Then returns null', () => {
    expect(readConsent(throwingStorage)).toBe(null)
  })
})

describe('writeConsent', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('Given "accepted" When write Then persists "accepted" to storage', () => {
    const s = new MemoryStorage()
    const target = new EventTarget()
    writeConsent('accepted', s, target)
    expect(s.getItem(STORAGE_KEY)).toBe('accepted')
  })

  it('Given "rejected" When write Then persists "rejected" to storage', () => {
    const s = new MemoryStorage()
    const target = new EventTarget()
    writeConsent('rejected', s, target)
    expect(s.getItem(STORAGE_KEY)).toBe('rejected')
  })

  it('Given "accepted" When write Then dispatches consent-changed with value', () => {
    const s = new MemoryStorage()
    const target = new EventTarget()
    const received: string[] = []
    target.addEventListener(CONSENT_CHANGED_EVENT, (event) => {
      received.push((event as CustomEvent<{ value: string }>).detail.value)
    })
    writeConsent('accepted', s, target)
    expect(received).toEqual(['accepted'])
  })

  it('Given "rejected" When write Then dispatches consent-changed with value', () => {
    const s = new MemoryStorage()
    const target = new EventTarget()
    const received: string[] = []
    target.addEventListener(CONSENT_CHANGED_EVENT, (event) => {
      received.push((event as CustomEvent<{ value: string }>).detail.value)
    })
    writeConsent('rejected', s, target)
    expect(received).toEqual(['rejected'])
  })

  it('Given storage that throws When write Then still dispatches the event', () => {
    const target = new EventTarget()
    const received: string[] = []
    target.addEventListener(CONSENT_CHANGED_EVENT, (event) => {
      received.push((event as CustomEvent<{ value: string }>).detail.value)
    })
    writeConsent('accepted', throwingStorage, target)
    expect(received).toEqual(['accepted'])
  })

  it('Given no explicit target When write Then dispatches on document', () => {
    const s = new MemoryStorage()
    const received: string[] = []
    const handler = (event: Event) => {
      received.push((event as CustomEvent<{ value: string }>).detail.value)
    }
    document.addEventListener(CONSENT_CHANGED_EVENT, handler)
    writeConsent('rejected', s)
    document.removeEventListener(CONSENT_CHANGED_EVENT, handler)
    expect(received).toEqual(['rejected'])
  })
})
