/**
 * @module cookie-consent
 * @description Logica pura del consentimiento GDPR del portfolio. El banner
 *   `CookieBanner.astro` y el enlace de gestion del `Footer` consumen estas
 *   funciones; mantenerlas en un modulo TS aparte las vuelve testeables sin
 *   renderear el componente Astro.
 *
 *   El consentimiento vive en localStorage (key `cf_consent`, valores
 *   `accepted` | `rejected`). NO se usan cookies. La key NO debe cambiar:
 *   `TrackingPixel.astro` la lee para decidir si emite eventos.
 *
 *   Los textos del banner NO viven aqui: estan en el YAML i18n
 *   (`elements.<lang>.yaml`, rama `components.cookieBanner`) y se pasan al
 *   componente como prop.
 *
 *   API:
 *     readConsent(storage?)        - lee el consentimiento persistido
 *     writeConsent(value, ...)     - persiste y despacha consent-changed
 */

/**
 * @type ConsentValue
 * @description Valor del consentimiento persistido en localStorage.
 */
export type ConsentValue = 'accepted' | 'rejected'

/** Key de localStorage. NO cambiar: TrackingPixel.astro la lee. */
export const STORAGE_KEY = 'cf_consent'

/** Nombre del evento que se despacha al cambiar el consentimiento. */
export const CONSENT_CHANGED_EVENT = 'portfolio:consent-changed'

/** Nombre del evento que pide reabrir el banner (lo emite el Footer). */
export const REOPEN_BANNER_EVENT = 'portfolio:consent-reopen'

/**
 * @function isConsentValue
 * @description Type guard para `ConsentValue`.
 */
export function isConsentValue(value: unknown): value is ConsentValue {
  return value === 'accepted' || value === 'rejected'
}

/**
 * @function readConsent
 * @description Lee el consentimiento persistido. `null` si el usuario aun no
 *   respondio o si localStorage no esta disponible (Safari private mode).
 */
export function readConsent(storage?: Storage): ConsentValue | null {
  try {
    const s = storage ?? globalThis.localStorage
    const raw = s?.getItem(STORAGE_KEY)
    return isConsentValue(raw) ? raw : null
  } catch {
    return null
  }
}

/**
 * @function writeConsent
 * @description Persiste el consentimiento en localStorage y despacha el
 *   evento `portfolio:consent-changed` para que `TrackingPixel.astro`
 *   reaccione. Si localStorage falla, igual se despacha el evento.
 *
 * @example
 *   writeConsent('accepted')   // persiste + dispara consent-changed
 *   writeConsent('rejected')   // persiste + dispara consent-changed
 */
export function writeConsent(
  value: ConsentValue,
  storage?: Storage,
  target?: EventTarget,
): void {
  try {
    const s = storage ?? globalThis.localStorage
    s?.setItem(STORAGE_KEY, value)
  } catch {
    /* storage unavailable (private mode); el evento igual se despacha */
  }
  const dispatcher = target ?? globalThis.document
  dispatcher?.dispatchEvent(
    new CustomEvent<{ value: ConsentValue }>(CONSENT_CHANGED_EVENT, {
      detail: { value },
    }),
  )
}
