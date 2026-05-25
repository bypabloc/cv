/**
 * @module track-event
 * @description API unica de emision de eventos de tracking del frontend.
 *
 *   `trackEvent(eventTypeId, props?)` arma el payload `POST /track`: genera un
 *   `event_id` (UUIDv4 por evento, para idempotencia en reintentos de
 *   sendBeacon), adjunta `session_id` (localStorage `cf_session`, la misma
 *   key del pixel page_load), `page_url`, y `event_props` opcional.
 *
 *   Tracking always-on: NO hay gating de consentimiento. Privacy stance:
 *   no PII, no cookies, anonimo, TTL 60 dias en DynamoDB. El unico estado
 *   persistido del lado del cliente es `cf_session` (UUID por sesion).
 *
 *   `TrackingPixel.astro` y los inicializadores `initClickTracking` /
 *   `initScrollDepth` usan este modulo: nadie duplica la logica de envio.
 *
 * @example
 *   import { configureTracking, trackEvent } from '@portfolio/ui/lib/track-event'
 *   configureTracking({ apiEndpoint: 'https://api.example.com', niche: 'generic' })
 *   trackEvent(EVENT_TYPES.CTA_CLICK, { href: '/contact' })
 */

const STORAGE_SESSION = 'cf_session'

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
 *
 *   Spec tracking-data-completeness: page_path, page_url, page_title,
 *   viewport_width, viewport_height y utm_source/medium/campaign/content
 *   son REQUIRED (string vacio cuando no aplica). `referrer` queda
 *   best-effort (string vacio si `document.referrer` esta vacio).
 *   `device_pixel_ratio` y `utm_term` son opcionales con defaults.
 */
export interface TrackEventPayload {
  // El handler HTTP generico del backend exige operation y action en el
  // body. Son constantes para tracking pero el shape los requiere.
  operation: 'tracking'
  action: 'track'
  session_id: string
  event_id: string
  event_type_id: string
  // Page metadata (required en el backend)
  page_url: string
  page_path: string
  page_title: string
  // Best-effort: '' cuando document.referrer esta vacio
  referrer: string
  // UTM params del query string (required en el payload, '' cuando no aplica)
  utm_source: string
  utm_medium: string
  utm_campaign: string
  utm_content: string
  utm_term?: string
  // Viewport del browser real (required en el backend)
  viewport_width: number
  viewport_height: number
  device_pixel_ratio?: number
  // Niche del subdominio
  niche: string
  event_props?: Record<string, unknown>
}

/**
 * @function getPageMetadata
 * @description Captura page_path, page_url, page_title, referrer del
 *   document/location del browser. Funcion pura (testeable).
 */
export function getPageMetadata(): {
  page_url: string
  page_path: string
  page_title: string
  referrer: string
} {
  const loc = globalThis.location
  const doc = globalThis.document
  return {
    page_url: (loc?.href ?? '').slice(0, 500),
    page_path: (loc?.pathname ?? '').slice(0, 300),
    page_title: (doc?.title ?? '').slice(0, 200),
    referrer: (doc?.referrer ?? '').slice(0, 500),
  }
}

/**
 * @function parseUtmParams
 * @description Extrae los 4 utm_* del query string del `searchUrl`. Si la
 *   URL no trae alguno, devuelve string vacio (no `undefined`). Tope de
 *   100 chars por valor (matchea el max_length del Pydantic).
 */
export function parseUtmParams(searchUrl?: string): {
  utm_source: string
  utm_medium: string
  utm_campaign: string
  utm_content: string
} {
  const source = searchUrl ?? globalThis.location?.search ?? ''
  let params: URLSearchParams
  try {
    params = new URLSearchParams(source)
  } catch {
    params = new URLSearchParams()
  }
  const pick = (k: string): string => (params.get(k) ?? '').slice(0, 100)
  return {
    utm_source: pick('utm_source'),
    utm_medium: pick('utm_medium'),
    utm_campaign: pick('utm_campaign'),
    utm_content: pick('utm_content'),
  }
}

/**
 * @function getViewport
 * @description Captura viewport_width/height y devicePixelRatio del
 *   browser. Devuelve `0` si window no esta disponible (SSR / tests).
 */
export function getViewport(): {
  viewport_width: number
  viewport_height: number
  device_pixel_ratio: number
} {
  const win = globalThis.window as (Window & typeof globalThis) | undefined
  return {
    viewport_width: Math.trunc(win?.innerWidth ?? 0),
    viewport_height: Math.trunc(win?.innerHeight ?? 0),
    device_pixel_ratio: Number(win?.devicePixelRatio ?? 1) || 1,
  }
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
  const pageMeta = getPageMetadata()
  const utm = parseUtmParams()
  const viewport = getViewport()
  const payload: TrackEventPayload = {
    operation: 'tracking',
    action: 'track',
    session_id: getSessionId(),
    event_id: generateEventId(),
    event_type_id: eventTypeId,
    ...pageMeta,
    ...utm,
    ...viewport,
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
 * @description Emite un evento de tracking. Always-on: sin gating. Retorna
 *   `false` solo si no hay endpoint configurado o si `sendBeacon` reporta
 *   fallo.
 *
 * @param {string} eventTypeId - UUID del tipo de evento (de `EVENT_TYPES`)
 * @param {Record<string, unknown>} [props] - contexto del evento
 * @returns {boolean} true si se emitio, false si no se pudo entregar
 *
 * @example
 *   trackEvent(EVENT_TYPES.THEME_TOGGLE, { theme: 'dark' })
 */
export function trackEvent(
  eventTypeId: string,
  props?: Record<string, unknown>,
): boolean {
  const payload = buildTrackPayload(eventTypeId, props)
  return sendBeaconPayload(payload)
}
