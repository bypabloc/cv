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
 *   API:
 *     readConsent(storage?)        - lee el consentimiento persistido
 *     writeConsent(value, ...)     - persiste y despacha consent-changed
 *     getBannerCopy(locale)        - textos i18n del banner por locale
 *     getManageConsentLabel(...)   - etiqueta del enlace del Footer por locale
 */

/**
 * @type ConsentValue
 * @description Valor del consentimiento persistido en localStorage.
 */
export type ConsentValue = 'accepted' | 'rejected'

/**
 * @type BannerLocale
 * @description Locale soportado por los textos del banner.
 */
export type BannerLocale = 'es' | 'en'

/**
 * @type BannerCopy
 * @description Conjunto de strings i18n que renderiza el banner.
 */
export interface BannerCopy {
  /** Etiqueta accesible del dialog (aria-label). */
  ariaLabel: string
  /** Texto del cuerpo del banner (parte previa al fragmento destacado). */
  bodyLead: string
  /** Fragmento destacado dentro del cuerpo (va en <strong>). */
  bodyStrong: string
  /** Texto del cuerpo posterior al fragmento destacado. */
  bodyTail: string
  /** Etiqueta del boton de aceptacion. */
  accept: string
  /** Etiqueta del boton de rechazo. */
  reject: string
}

/** Key de localStorage. NO cambiar: TrackingPixel.astro la lee. */
export const STORAGE_KEY = 'cf_consent'

/** Nombre del evento que se despacha al cambiar el consentimiento. */
export const CONSENT_CHANGED_EVENT = 'portfolio:consent-changed'

/** Nombre del evento que pide reabrir el banner (lo emite el Footer). */
export const REOPEN_BANNER_EVENT = 'portfolio:consent-reopen'

const BANNER_COPY: Record<BannerLocale, BannerCopy> = {
  es: {
    ariaLabel: 'Consentimiento de analytics',
    bodyLead: 'Este sitio usa ',
    bodyStrong: 'analytics propios privacy-friendly',
    bodyTail:
      ' (sin cookies de terceros, los datos se auto-borran en 60 dias). ' +
      '¿Permitis recolectar tu visita para mejorar el contenido?',
    accept: 'Aceptar',
    reject: 'Rechazar',
  },
  en: {
    ariaLabel: 'Analytics consent',
    bodyLead: 'This site uses ',
    bodyStrong: 'privacy-friendly first-party analytics',
    bodyTail:
      ' (no third-party cookies, data auto-deletes after 60 days). ' +
      'May we collect your visit to improve the content?',
    accept: 'Accept',
    reject: 'Reject',
  },
}

const MANAGE_CONSENT_LABEL: Record<BannerLocale, string> = {
  es: 'Gestionar consentimiento',
  en: 'Manage consent',
}

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

/**
 * @function getBannerCopy
 * @description Devuelve los textos i18n del banner para el locale dado.
 *   Cualquier locale no soportado cae a 'es'.
 *
 * @example
 *   getBannerCopy('en').accept   // "Accept"
 *   getBannerCopy('es').accept   // "Aceptar"
 */
export function getBannerCopy(locale: BannerLocale): BannerCopy {
  return BANNER_COPY[locale] ?? BANNER_COPY.es
}

/**
 * @function getManageConsentLabel
 * @description Etiqueta del enlace del Footer que reabre el banner.
 *
 * @example
 *   getManageConsentLabel('es')  // "Gestionar consentimiento"
 *   getManageConsentLabel('en')  // "Manage consent"
 */
export function getManageConsentLabel(locale: BannerLocale): string {
  return MANAGE_CONSENT_LABEL[locale] ?? MANAGE_CONSENT_LABEL.es
}
