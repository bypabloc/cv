/**
 * @module track-event
 * @description API unica de emision de eventos de tracking del frontend.
 *
 *   `trackEvent(eventTypeId, props?)` arma el payload `POST /track`: genera un
 *   `event_id` (UUIDv4 por evento, para idempotencia en reintentos de
 *   sendBeacon), adjunta `session_id` (localStorage `cf_session`, la misma
 *   key del pixel page_load), `page_url`, y `event_props` opcional.
 *
 *   GATING: solo emite si hay consentimiento — `localStorage.cf_consent`
 *   debe ser `'accepted'`. El flag de QA `?cf_track=force` lo bypassa (para
 *   E2E). Sin consentimiento ni flag: cero eventos (GDPR por defecto).
 *
 *   `TrackingPixel.astro` y los inicializadores `initClickTracking` /
 *   `initScrollDepth` usan este modulo: nadie duplica la logica de envio.
 *
 * @example
 *   import { configureTracking, trackEvent } from '@portfolio/ui/lib/track-event'
 *   configureTracking({ apiEndpoint: 'https://api.example.com', niche: 'generic' })
 *   trackEvent(EVENT_TYPES.CTA_CLICK, { href: '/contact' })
 */

const STORAGE_CONSENT = 'cf_consent'
const STORAGE_SESSION = 'cf_session'
const CONSENT_ACCEPTED = 'accepted'
const QA_FLAG = 'cf_track'
const QA_FLAG_VALUE = 'force'

/**
 * @type TrackingConfig
 * @description Configuracion del modulo: endpoint del API Gateway + niche.
 */
export interface TrackingConfig {
  /** URL base del API Gateway (sin `/track`). */
  apiEndpoint: string
  /** Niche del subdominio (se adjunta al payload). */
  niche?: string
}

/**
 * @type TrackEventPayload
 * @description Forma del body que se envia a `POST /track`.
 */
export interface TrackEventPayload {
  // El handler HTTP generico del backend exige operation y action en el
  // body. Son constantes para tracking pero el shape los requiere.
  operation: 'tracking'
  action: 'track'
  session_id: string
  event_id: string
  event_type_id: string
  page_url: string
  niche: string
  event_props?: Record<string, unknown>
}

let config: TrackingConfig | null = null

/**
 * @function configureTracking
 * @description Setea el endpoint + niche del modulo. Debe invocarse una vez
 *   antes del primer `trackEvent` (lo hace `TrackingPixel.astro`).
 */
export function configureTracking(next: TrackingConfig): void {
  config = next
}

/**
 * @function resetTrackingConfig
 * @description Limpia la configuracion. Solo para aislamiento entre tests.
 */
export function resetTrackingConfig(): void {
  config = null
}

/**
 * @function generateEventId
 * @description UUIDv4 por evento. Usa `crypto.randomUUID` con fallback para
 *   browsers viejos. Se devuelve sin guiones para encajar en el limite que
 *   valida el backend.
 *
 * @returns {string} identificador unico del evento (hex, sin guiones)
 */
export function generateEventId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID().replace(/-/g, '')
  }
  const rand = (): string => Math.random().toString(36).slice(2)
  return `${Date.now().toString(36)}${rand()}${rand()}`
}

/**
 * @function isTrackingForced
 * @description True si la URL lleva `?cf_track=force` (bypass de QA del
 *   gating de consentimiento, usado por los tests E2E).
 */
export function isTrackingForced(): boolean {
  try {
    const search = globalThis.location?.search ?? ''
    return new URLSearchParams(search).get(QA_FLAG) === QA_FLAG_VALUE
  } catch {
    return false
  }
}

/**
 * @function hasTrackingConsent
 * @description True si el usuario acepto el tracking (`cf_consent` =
 *   `'accepted'`) o si la URL lleva el flag de QA `?cf_track=force`.
 */
export function hasTrackingConsent(): boolean {
  if (isTrackingForced()) return true
  try {
    return localStorage.getItem(STORAGE_CONSENT) === CONSENT_ACCEPTED
  } catch {
    return false
  }
}

/**
 * @function getSessionId
 * @description Lee (o crea) el `session_id` persistido en localStorage
 *   `cf_session` — la misma key del pixel page_load, para que clicks,
 *   scroll y page_load compartan sesion.
 */
export function getSessionId(): string {
  try {
    let sid = localStorage.getItem(STORAGE_SESSION)
    if (!sid || sid.length < 20) {
      sid = generateEventId()
      localStorage.setItem(STORAGE_SESSION, sid)
    }
    return sid
  } catch {
    return `nostorage-${generateEventId()}`
  }
}

/**
 * @function buildTrackPayload
 * @description Arma el payload `POST /track` para un evento. Funcion pura:
 *   no envia nada (separada de `trackEvent` para poder testear el shape).
 *
 * @param {string} eventTypeId - UUID del tipo de evento (de `EVENT_TYPES`)
 * @param {Record<string, unknown>} [props] - datos del evento (`event_props`)
 * @returns {TrackEventPayload} body listo para serializar
 */
export function buildTrackPayload(
  eventTypeId: string,
  props?: Record<string, unknown>,
): TrackEventPayload {
  const payload: TrackEventPayload = {
    operation: 'tracking',
    action: 'track',
    session_id: getSessionId(),
    event_id: generateEventId(),
    event_type_id: eventTypeId,
    page_url: (globalThis.location?.href ?? '').slice(0, 500),
    niche: config?.niche ?? 'generic',
  }
  if (props && Object.keys(props).length > 0) {
    payload.event_props = props
  }
  return payload
}

/**
 * @function sendBeaconPayload
 * @description Envia el body a `POST /track` via `navigator.sendBeacon`
 *   (sigue funcionando si el usuario cierra la pestana), con fallback a
 *   `fetch` keepalive. Fire-and-forget: cualquier error se ignora.
 *
 *   El Blob va con `type: 'text/plain'` a proposito: `text/plain` es un
 *   Content-Type CORS-safelisted, asi que `sendBeacon` envia una request
 *   SIMPLE (sin preflight). Con `application/json` el browser dispara
 *   preflight y el modo `ping` de sendBeacon falla con CORS error tras el
 *   preflight. El body sigue siendo JSON serializado; el backend `/track`
 *   parsea con `json.loads()` sin mirar el Content-Type.
 *
 * @returns {boolean} true si se entrego (a beacon o fetch), false si no
 */
export function sendBeaconPayload(payload: TrackEventPayload): boolean {
  if (!config?.apiEndpoint) return false
  const url = `${config.apiEndpoint}/track`
  const body = JSON.stringify(payload)
  try {
    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      // text/plain evita el preflight CORS que rompe el modo `ping`.
      const blob = new Blob([body], { type: 'text/plain' })
      return navigator.sendBeacon(url, blob)
    }
  } catch {
    // continua con el fallback fetch
  }
  try {
    // El fallback fetch tambien usa text/plain: mismo motivo (request
    // simple, sin preflight). El backend parsea el body como JSON.
    void fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body,
      keepalive: true,
    }).catch(() => {
      // tracking es fire-and-forget
    })
    return true
  } catch {
    return false
  }
}

/**
 * @function trackEvent
 * @description Emite un evento de tracking. GATING: si no hay consentimiento
 *   ni el flag `?cf_track=force`, NO emite nada y retorna false.
 *
 * @param {string} eventTypeId - UUID del tipo de evento (de `EVENT_TYPES`)
 * @param {Record<string, unknown>} [props] - contexto del evento
 * @returns {boolean} true si se emitio, false si el gating lo bloqueo
 *
 * @example
 *   trackEvent(EVENT_TYPES.THEME_TOGGLE, { theme: 'dark' })
 */
export function trackEvent(
  eventTypeId: string,
  props?: Record<string, unknown>,
): boolean {
  if (!hasTrackingConsent()) return false
  const payload = buildTrackPayload(eventTypeId, props)
  return sendBeaconPayload(payload)
}
