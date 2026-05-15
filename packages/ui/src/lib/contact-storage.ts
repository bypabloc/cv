/**
 * @module contact-storage
 * @description Persistencia del estado "ya envio el form de contacto" usando
 *   localStorage (fuente de verdad) + cookie compartida entre subdominios
 *   `.the-full-stack.com` (para que el estado se propague entre nichos).
 *
 *   localStorage es por subdominio (cada *.the-full-stack.com tiene su propio
 *   storage), asi que la cookie compartida es la unica forma de evitar que el
 *   user vea el form de nuevo al saltar entre nichos. Cuando otro subdominio
 *   detecta la cookie pero no tiene localStorage, hace rehidratacion.
 *
 *   TTL: 7 dias.
 */

/**
 * Estructura serializada del registro de contacto enviado.
 */
export interface ContactRecord {
  contactId: string
  /** Epoch ms del envio */
  sentAt: number
  /** Epoch ms en que expira el registro (sentAt + TTL_MS) */
  expiresAt: number
}

const STORAGE_KEY = 'contact_sent'
const COOKIE_NAME = 'contact_sent'
export const TTL_MS = 7 * 24 * 60 * 60 * 1000

/**
 * Dominio raiz para la cookie compartida. Se calcula en runtime para que
 * en `*.localhost` (dev) no se setee `Domain=` (los browsers no comparten
 * cookies entre subdominios de `localhost` por especificacion).
 */
function getCookieDomain(hostname: string): string | null {
  if (!hostname || hostname === 'localhost') return null
  if (hostname.endsWith('.localhost')) return null
  if (/^[\d.]+$/u.test(hostname)) return null
  const parts = hostname.split('.')
  if (parts.length < 2) return null
  return `.${parts.slice(-2).join('.')}`
}

function isSecureProtocol(protocol: string): boolean {
  return protocol === 'https:'
}

/**
 * @function readCookie
 * @description Lee el valor crudo de una cookie por nombre.
 * @internal exportada solo para tests
 */
export function readCookie(name: string, cookieString: string): string | null {
  if (!cookieString) return null
  const pattern = new RegExp(
    `(?:^|;\\s*)${name.replace(/[.*+?^${}()|[\]\\]/gu, '\\$&')}=([^;]*)`,
    'u',
  )
  const match = cookieString.match(pattern)
  if (!match?.[1]) return null
  try {
    return decodeURIComponent(match[1])
  } catch {
    return null
  }
}

/**
 * @function buildCookieString
 * @description Construye el string de cookie a setear via `document.cookie =`.
 *   Exportado para tests.
 */
export function buildCookieString(
  value: string,
  options: {
    maxAgeSeconds: number
    hostname: string
    protocol: string
    path?: string
  },
): string {
  const parts = [`${COOKIE_NAME}=${encodeURIComponent(value)}`]
  parts.push(`Max-Age=${options.maxAgeSeconds}`)
  parts.push(`Path=${options.path ?? '/'}`)
  parts.push('SameSite=Lax')
  const domain = getCookieDomain(options.hostname)
  if (domain) parts.push(`Domain=${domain}`)
  if (isSecureProtocol(options.protocol)) parts.push('Secure')
  return parts.join('; ')
}

/**
 * @function buildExpiredCookieString
 * @description String para borrar la cookie (Max-Age=0). Mismo Domain/Path
 *   que el setter, sino el browser no la elimina.
 */
export function buildExpiredCookieString(options: {
  hostname: string
  protocol: string
  path?: string
}): string {
  const parts = [`${COOKIE_NAME}=`]
  parts.push('Max-Age=0')
  parts.push(`Path=${options.path ?? '/'}`)
  parts.push('SameSite=Lax')
  const domain = getCookieDomain(options.hostname)
  if (domain) parts.push(`Domain=${domain}`)
  if (isSecureProtocol(options.protocol)) parts.push('Secure')
  return parts.join('; ')
}

/**
 * @function parseRecord
 * @description Valida y parsea un registro desde string JSON. Retorna `null`
 *   si esta mal formado o expirado. Exportado para tests.
 */
export function parseRecord(
  raw: string | null,
  now: number,
): ContactRecord | null {
  if (!raw) return null
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return null
  }
  if (typeof parsed !== 'object' || parsed === null) return null
  const obj = parsed as Record<string, unknown>
  const contactId = obj.contactId
  const sentAt = obj.sentAt
  const expiresAt = obj.expiresAt
  if (typeof contactId !== 'string' || contactId.length === 0) return null
  if (typeof sentAt !== 'number' || !Number.isFinite(sentAt)) return null
  if (typeof expiresAt !== 'number' || !Number.isFinite(expiresAt)) return null
  if (expiresAt <= now) return null
  return { contactId, sentAt, expiresAt }
}

/**
 * @function readContactRecord
 * @description Lee el registro del contacto enviado, combinando localStorage
 *   (rapido) + cookie (fallback cross-subdomain). Si la cookie tiene un
 *   registro vivo pero localStorage no, rehidrata localStorage.
 *
 * @returns Registro vivo (no expirado) o `null`.
 */
export function readContactRecord(): ContactRecord | null {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return null
  }
  const now = Date.now()

  // 1. Intentar localStorage primero (fuente local de verdad)
  let fromStorage: ContactRecord | null = null
  try {
    fromStorage = parseRecord(window.localStorage.getItem(STORAGE_KEY), now)
  } catch {
    // Safari private mode, etc. — silencioso, seguimos con cookie
  }
  if (fromStorage) return fromStorage

  // 2. Fallback: cookie compartida
  const fromCookie = parseRecord(readCookie(COOKIE_NAME, document.cookie), now)
  if (fromCookie) {
    // Rehidratar localStorage para evitar leer la cookie en cada nav
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(fromCookie))
    } catch {
      // ignorar
    }
    return fromCookie
  }

  return null
}

/**
 * @function saveContactRecord
 * @description Persiste el registro en localStorage + cookie compartida.
 *
 * @param contactId - UUID retornado por el Lambda (campo `contact_id`)
 * @param now - Epoch ms del envio (default `Date.now()`). Inyectable para tests.
 */
export function saveContactRecord(
  contactId: string,
  now: number = Date.now(),
): ContactRecord {
  const record: ContactRecord = {
    contactId,
    sentAt: now,
    expiresAt: now + TTL_MS,
  }
  const json = JSON.stringify(record)

  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(STORAGE_KEY, json)
    } catch {
      // ignorar (private mode)
    }
  }

  if (typeof document !== 'undefined' && typeof window !== 'undefined') {
    // Cookie Store API no esta disponible en Safari ni Firefox estables,
    // por eso usamos la API legacy de document.cookie.
    // biome-ignore lint/suspicious/noDocumentCookie: cross-browser fallback
    document.cookie = buildCookieString(json, {
      maxAgeSeconds: Math.floor(TTL_MS / 1000),
      hostname: window.location.hostname,
      protocol: window.location.protocol,
    })
  }

  return record
}

/**
 * @function clearContactRecord
 * @description Borra el registro de localStorage + cookie. Se llama cuando el
 *   user clickea "Enviar otro mensaje".
 */
export function clearContactRecord(): void {
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignorar
    }
  }
  if (typeof document !== 'undefined' && typeof window !== 'undefined') {
    // biome-ignore lint/suspicious/noDocumentCookie: cross-browser fallback
    document.cookie = buildExpiredCookieString({
      hostname: window.location.hostname,
      protocol: window.location.protocol,
    })
  }
}

/**
 * @function formatSentDate
 * @description Formatea el `sentAt` como fecha legible en es-CL (ej.
 *   "15 de mayo de 2026"). Aislado en su propia funcion para facilitar
 *   testing.
 */
export function formatSentDate(sentAt: number, locale = 'es-CL'): string {
  try {
    return new Intl.DateTimeFormat(locale, {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(new Date(sentAt))
  } catch {
    return new Date(sentAt).toISOString().slice(0, 10)
  }
}
