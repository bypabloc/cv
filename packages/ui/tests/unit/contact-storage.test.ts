/**
 * @description Tests para contact-storage: parseRecord, readCookie,
 *   buildCookieString, save/read/clearContactRecord. Cubre flujo single-domain
 *   (localStorage) y cross-subdomain (cookie compartida).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buildCookieString,
  buildExpiredCookieString,
  clearContactRecord,
  formatSentDate,
  parseRecord,
  readContactRecord,
  readCookie,
  saveContactRecord,
  TTL_MS,
} from '../../src/lib/contact-storage'

const NOW = 1715731200000

describe('parseRecord', () => {
  it('Given null When parse Then returns null', () => {
    expect(parseRecord(null, NOW)).toBe(null)
  })

  it('Given invalid JSON When parse Then returns null', () => {
    expect(parseRecord('not-json', NOW)).toBe(null)
  })

  it('Given missing contactId When parse Then returns null', () => {
    const raw = JSON.stringify({ sentAt: NOW, expiresAt: NOW + TTL_MS })
    expect(parseRecord(raw, NOW)).toBe(null)
  })

  it('Given expired record When parse Then returns null', () => {
    const raw = JSON.stringify({
      contactId: 'abc',
      sentAt: NOW - TTL_MS - 1,
      expiresAt: NOW - 1,
    })
    expect(parseRecord(raw, NOW)).toBe(null)
  })

  it('Given valid record When parse Then returns parsed object', () => {
    const raw = JSON.stringify({
      contactId: 'abc-123',
      sentAt: NOW,
      expiresAt: NOW + TTL_MS,
    })
    const result = parseRecord(raw, NOW)
    expect(result).toEqual({
      contactId: 'abc-123',
      sentAt: NOW,
      expiresAt: NOW + TTL_MS,
    })
  })
})

describe('readCookie', () => {
  it('Given empty cookie string When read Then returns null', () => {
    expect(readCookie('contact_sent', '')).toBe(null)
  })

  it('Given cookie with target name When read Then returns decoded value', () => {
    const value = encodeURIComponent('{"foo":"bar"}')
    const cookieString = `other=1; contact_sent=${value}; another=2`
    expect(readCookie('contact_sent', cookieString)).toBe('{"foo":"bar"}')
  })

  it('Given cookie without target name When read Then returns null', () => {
    expect(readCookie('contact_sent', 'other=1; another=2')).toBe(null)
  })

  it('Given malformed URI encoding When read Then returns null', () => {
    // %ZZ no es un escape valido -> decodeURIComponent lanza
    expect(readCookie('contact_sent', 'contact_sent=%ZZ')).toBe(null)
  })
})

describe('buildCookieString', () => {
  it('Given the-full-stack.com hostname When build Then includes Domain=.the-full-stack.com', () => {
    const result = buildCookieString('value-x', {
      maxAgeSeconds: 604800,
      hostname: 'fintech.portfolio.the-full-stack.com',
      protocol: 'https:',
    })
    expect(result).toBe(
      'contact_sent=value-x; Max-Age=604800; Path=/; SameSite=Lax; Domain=.the-full-stack.com; Secure',
    )
  })

  it('Given localhost When build Then omits Domain', () => {
    const result = buildCookieString('v', {
      maxAgeSeconds: 60,
      hostname: 'localhost',
      protocol: 'http:',
    })
    expect(result).toBe('contact_sent=v; Max-Age=60; Path=/; SameSite=Lax')
  })

  it('Given *.localhost When build Then omits Domain', () => {
    const result = buildCookieString('v', {
      maxAgeSeconds: 60,
      hostname: 'fintech.localhost',
      protocol: 'http:',
    })
    expect(result).toBe('contact_sent=v; Max-Age=60; Path=/; SameSite=Lax')
  })

  it('Given IP address When build Then omits Domain', () => {
    const result = buildCookieString('v', {
      maxAgeSeconds: 60,
      hostname: '192.168.1.10',
      protocol: 'http:',
    })
    expect(result).toBe('contact_sent=v; Max-Age=60; Path=/; SameSite=Lax')
  })

  it('Given value with special chars When build Then encodes value', () => {
    const result = buildCookieString('a b;c', {
      maxAgeSeconds: 60,
      hostname: 'the-full-stack.com',
      protocol: 'https:',
    })
    expect(result).toBe(
      'contact_sent=a%20b%3Bc; Max-Age=60; Path=/; SameSite=Lax; Domain=.the-full-stack.com; Secure',
    )
  })
})

describe('buildExpiredCookieString', () => {
  it('Given hostname When build expired Then uses Max-Age=0 and same Domain', () => {
    const result = buildExpiredCookieString({
      hostname: 'fintech.portfolio.the-full-stack.com',
      protocol: 'https:',
    })
    expect(result).toBe(
      'contact_sent=; Max-Age=0; Path=/; SameSite=Lax; Domain=.the-full-stack.com; Secure',
    )
  })
})

describe('saveContactRecord + readContactRecord (jsdom)', () => {
  let dateSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    window.localStorage.clear()
    // biome-ignore lint/suspicious/noDocumentCookie: test setup
    document.cookie = 'contact_sent=; Max-Age=0; Path=/'
    dateSpy = vi.spyOn(Date, 'now').mockReturnValue(NOW)
  })

  afterEach(() => {
    dateSpy.mockRestore()
  })

  it('Given saved record When read Then returns same record', () => {
    saveContactRecord('019e28fc-b97d-7d79-91a5-44c9b19465b4', NOW)
    const result = readContactRecord()
    expect(result).toEqual({
      contactId: '019e28fc-b97d-7d79-91a5-44c9b19465b4',
      sentAt: NOW,
      expiresAt: NOW + TTL_MS,
    })
  })

  it('Given save Then localStorage has JSON record', () => {
    saveContactRecord('test-id', NOW)
    const raw = window.localStorage.getItem('contact_sent')
    expect(raw).toBe(
      JSON.stringify({
        contactId: 'test-id',
        sentAt: NOW,
        expiresAt: NOW + TTL_MS,
      }),
    )
  })

  it('Given no record When read Then returns null', () => {
    expect(readContactRecord()).toBe(null)
  })

  it('Given cleared record When read Then returns null', () => {
    saveContactRecord('to-clear', NOW)
    clearContactRecord()
    expect(readContactRecord()).toBe(null)
    expect(window.localStorage.getItem('contact_sent')).toBe(null)
  })

  it('Given only cookie present When read Then rehydrates localStorage', () => {
    // Simular llegada cross-subdomain: cookie pero no localStorage
    const record = JSON.stringify({
      contactId: 'from-cookie',
      sentAt: NOW,
      expiresAt: NOW + TTL_MS,
    })
    // biome-ignore lint/suspicious/noDocumentCookie: test setup
    document.cookie = `contact_sent=${encodeURIComponent(record)}; Path=/`
    expect(window.localStorage.getItem('contact_sent')).toBe(null)

    const result = readContactRecord()
    expect(result).toEqual({
      contactId: 'from-cookie',
      sentAt: NOW,
      expiresAt: NOW + TTL_MS,
    })
    expect(window.localStorage.getItem('contact_sent')).toBe(record)
  })

  it('Given expired localStorage record When read Then returns null', () => {
    const expired = JSON.stringify({
      contactId: 'old',
      sentAt: NOW - TTL_MS - 1000,
      expiresAt: NOW - 1000,
    })
    window.localStorage.setItem('contact_sent', expired)
    expect(readContactRecord()).toBe(null)
  })
})

describe('formatSentDate', () => {
  it('Given epoch ms and es-CL When format Then returns Spanish long date', () => {
    // 2026-05-15 (NOW=1715731200000 -> Tue May 14 2024 UTC; usamos un valor distinto)
    const epoch = Date.UTC(2026, 4, 15, 12, 0, 0) // 15 may 2026
    const formatted = formatSentDate(epoch, 'es-CL')
    expect(formatted).toBe('15 de mayo de 2026')
  })
})
