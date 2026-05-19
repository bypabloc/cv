/**
 * @component ContactFormReact
 * @description Form de contacto React 18: validacion Zod dinamica + POST al
 *   Lambda contact_form + persistencia (localStorage + cookie compartida) via
 *   `contact-storage`. Muestra card "ya enviaste" tras exito.
 *
 *   Bypass Turnstile para tests: si `window.__playwrightTurnstileBypass`
 *   es string, se envia como header `X-Turnstile-Bypass-Secret` y se omite
 *   el widget Turnstile (el frontend Astro NUNCA setea esa variable; solo
 *   Playwright via page.addInitScript en stage dev).
 *
 * @props {string} apiEndpoint - Full URL del POST /contact
 * @props {string} turnstileSitekey - Sitekey publica del widget Turnstile
 * @props {string} [niche] - Nicho del subdominio (generic | hub | fintech | ...)
 * @props {object} strings - Textos del form (components.contactForm del i18n)
 */
import type { ComponentsStrings } from '@portfolio/content'
import {
  type ChangeEvent,
  type FocusEvent,
  type FormEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from 'react'
import {
  buildContactPayload,
  type ContactFieldErrors,
  type ContactFormFieldName,
  ContactFormSchema,
  type ContactFormValues,
  emptyValues,
  getFieldErrors,
} from '../lib/contact-form-schema'
import {
  type ContactRecord,
  clearContactRecord,
  formatSentDate,
  readContactRecord,
  saveContactRecord,
} from '../lib/contact-storage'
import { configureTracking, trackEvent } from '../lib/track-event'

// `?render=explicit`: desactiva el render implicito de Turnstile (el que
// escanea el DOM buscando `.cf-turnstile`). El widget se monta solo via
// turnstile.render() explicito — evita el doble render y el warning
// "a widget already exists in this container".
const TURNSTILE_SCRIPT_URL =
  'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'

interface TurnstileGlobal {
  render?: (
    container: HTMLElement,
    options: {
      sitekey: string
      callback: (token: string) => void
      'error-callback'?: () => void
      'expired-callback'?: () => void
    },
  ) => string
  reset?: (widgetId?: string | Element | null) => void
  remove?: (widgetId?: string) => void
}

declare global {
  interface Window {
    turnstile?: TurnstileGlobal
    /**
     * Bypass secret para tests E2E. SOLO seteado por Playwright via
     * page.addInitScript. En produccion nunca llega al cliente.
     */
    __playwrightTurnstileBypass?: string
  }
}

/**
 * UUID del catalogo `event_types` para los 5 eventos del embudo de contacto.
 * Se resuelven en `ContactFormReact.astro` (server-side, desde
 * `@portfolio/content`) y se pasan como prop: asi el bundle del island no
 * importa `@portfolio/content` y Vite no re-optimiza el island en dev.
 */
interface FunnelEventTypes {
  contactView: string
  contactFormStart: string
  contactFormSubmit: string
  contactFormSuccess: string
  contactFormError: string
}

/** Textos i18n del form de contacto (rama `components.contactForm`). */
type ContactFormStrings = ComponentsStrings['contactForm']

interface ContactFormReactProps {
  apiEndpoint: string
  turnstileSitekey: string
  niche?: string
  funnelEventTypes: FunnelEventTypes
  strings: ContactFormStrings
}

interface ApiErrorBody {
  error?: string
  code?: string
  extra?: {
    errors?: Array<{
      type: string
      loc: (string | number)[]
      msg: string
      ctx?: Record<string, unknown>
    }>
  }
}

interface ApiSuccessBody {
  contact_id: string
  created_at: string
}

type StatusKind = 'idle' | 'submitting' | 'success' | 'error'

/** Mensaje de error HTTP segun el status, desde el YAML i18n. */
function errorMessageFor(
  httpStatus: number,
  strings: ContactFormStrings,
): string {
  if (httpStatus === 403) return strings.errorCaptchaInvalid
  if (httpStatus === 429) return strings.errorTooManyAttempts
  return strings.errorServer
}

/**
 * Lee `localStorage.cf_session` (la misma key que usa el TrackingPixel) para
 * enlazar el contacto con su journey de tracking (SPEC-202). Devuelve
 * `undefined` si no hay sesion (visitante que rechazo el tracking) o si el
 * acceso a localStorage falla — el form NUNCA debe romperse por esto.
 */
function readSessionId(): string | undefined {
  try {
    const sid = localStorage.getItem('cf_session')
    return sid && sid.length >= 20 ? sid : undefined
  } catch {
    return undefined
  }
}

function buildHeaders(bypassSecret: string): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (bypassSecret) headers['X-Turnstile-Bypass-Secret'] = bypassSecret
  return headers
}

async function parseJsonSafe(
  response: Response,
): Promise<(ApiErrorBody & ApiSuccessBody) | null> {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) return null
  try {
    return (await response.json()) as ApiErrorBody & ApiSuccessBody
  } catch {
    return null
  }
}

/**
 * Mapea errores Pydantic del backend a `ContactFieldErrors`. Los mensajes
 * salen del YAML i18n; `{min}` / `{max}` se interpolan con el `ctx` del error.
 */
function mapPydanticErrors(
  errors: NonNullable<NonNullable<ApiErrorBody['extra']>['errors']>,
  strings: ContactFormStrings,
): ContactFieldErrors {
  const result: ContactFieldErrors = {}
  for (const err of errors) {
    const field = [...err.loc]
      .reverse()
      .find((seg): seg is string => typeof seg === 'string')
    if (!field) continue
    if (result[field as ContactFormFieldName]) continue
    const min = String(err.ctx?.min_length ?? '?')
    const max = String(err.ctx?.max_length ?? '?')
    let msg: string
    switch (err.type) {
      case 'missing':
        msg = strings.validationRequired
        break
      case 'string_too_short':
        msg = strings.validationTooShort.replace('{min}', min)
        break
      case 'string_too_long':
        msg = strings.validationTooLong.replace('{max}', max)
        break
      case 'value_error':
      case 'value_error.email':
        msg = strings.validationEmail
        break
      default:
        msg = err.msg || strings.validationInvalid
    }
    result[field as ContactFormFieldName] = msg
  }
  return result
}

export default function ContactFormReact({
  apiEndpoint,
  turnstileSitekey,
  niche = 'generic',
  funnelEventTypes,
  strings,
}: ContactFormReactProps) {
  const reactId = useId()
  const [values, setValues] = useState<ContactFormValues>(emptyValues)
  const [errors, setErrors] = useState<ContactFieldErrors>({})
  const [status, setStatus] = useState<StatusKind>('idle')
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [sentRecord, setSentRecord] = useState<ContactRecord | null>(null)
  const [turnstileToken, setTurnstileToken] = useState<string>('')
  const turnstileContainerRef = useRef<HTMLDivElement | null>(null)
  const widgetIdRef = useRef<string | null>(null)

  // Detecta bypass de Playwright. Lo leemos una sola vez: el test lo inyecta
  // con addInitScript ANTES de que la pagina cargue.
  const bypassTokenRef = useRef<string>('')
  useEffect(() => {
    if (typeof window !== 'undefined' && window.__playwrightTurnstileBypass) {
      bypassTokenRef.current = window.__playwrightTurnstileBypass
    }
  }, [])

  // Embudo de contacto (SPEC-200): el primer foco en cualquier campo emite
  // `contact_form_start` una sola vez. Este flag evita repeticiones en focos
  // posteriores [AC-5].
  const formStartedRef = useRef<boolean>(false)

  // Configura la emision de eventos con el endpoint base + niche, y emite
  // `contact_view` al montar la pagina /contact [AC-4]. El gating de
  // consentimiento lo resuelve `trackEvent` internamente: si el visitante no
  // acepto el tracking, las llamadas son no-op.
  useEffect(() => {
    const base = apiEndpoint.replace(/\/contact$/, '')
    configureTracking({ apiEndpoint: base, niche })
    trackEvent(funnelEventTypes.contactView)
  }, [apiEndpoint, niche, funnelEventTypes.contactView])

  // Rehidratar estado "ya envio" desde localStorage/cookie
  useEffect(() => {
    const record = readContactRecord()
    if (record) setSentRecord(record)
  }, [])

  // Cargar script Turnstile + render widget (solo si NO hay bypass)
  useEffect(() => {
    if (bypassTokenRef.current) return
    if (sentRecord) return
    if (typeof window === 'undefined') return

    let cancelled = false

    function tryRender(): void {
      if (cancelled) return
      const t = window.turnstile
      const container = turnstileContainerRef.current
      if (!t?.render || !container) return
      if (widgetIdRef.current) return
      widgetIdRef.current = t.render(container, {
        sitekey: turnstileSitekey,
        callback: (token: string) => {
          setTurnstileToken(token)
        },
        'error-callback': () => {
          setTurnstileToken('')
          setStatus('error')
          setStatusMessage(strings.errorCaptchaLoad)
        },
        'expired-callback': () => {
          setTurnstileToken('')
        },
      })
    }

    // Si el script ya esta en la pagina, render directo. Si no, inyectar.
    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${TURNSTILE_SCRIPT_URL}"]`,
    )
    if (window.turnstile) {
      tryRender()
    } else if (existing) {
      existing.addEventListener('load', tryRender, { once: true })
    } else {
      const script = document.createElement('script')
      script.src = TURNSTILE_SCRIPT_URL
      script.async = true
      script.defer = true
      script.addEventListener('load', tryRender, { once: true })
      document.head.appendChild(script)
    }

    return () => {
      cancelled = true
      if (widgetIdRef.current && window.turnstile?.remove) {
        try {
          window.turnstile.remove(widgetIdRef.current)
        } catch {
          // ignorar
        }
        widgetIdRef.current = null
      }
    }
  }, [sentRecord, turnstileSitekey, strings.errorCaptchaLoad])

  /**
   * Valida un solo campo y actualiza errors[field]. Se llama on blur o
   * al detectar cambio en un campo que ya tenia error (UX progresiva).
   */
  const validateField = useCallback(
    (field: ContactFormFieldName, nextValues: ContactFormValues): void => {
      const fieldSchema = ContactFormSchema.shape[field]
      const result = fieldSchema.safeParse(nextValues[field])
      setErrors((prev) => {
        const next = { ...prev }
        if (result.success) {
          delete next[field]
        } else {
          next[field] =
            result.error.issues[0]?.message ?? strings.validationInvalid
        }
        return next
      })
    },
    [strings.validationInvalid],
  )

  const handleChange = useCallback(
    (
      e: ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ): void => {
      const name = e.target.name as ContactFormFieldName
      const value = e.target.value
      setValues((prev) => {
        const next = { ...prev, [name]: value }
        // Si ya habia error en este campo, re-validar al tipear
        if (errors[name]) {
          // Schedule en microtask para usar el "next" estado
          queueMicrotask(() => validateField(name, next))
        }
        return next
      })
    },
    [errors, validateField],
  )

  const handleBlur = useCallback(
    (
      e: FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
    ): void => {
      const name = e.target.name as ContactFormFieldName
      validateField(name, values)
    },
    [validateField, values],
  )

  /**
   * Foco delegado en el `<form>`: el primer foco en cualquier campo emite
   * `contact_form_start` una sola vez (el flag bloquea repeticiones) [AC-5].
   */
  const handleFormFocus = useCallback((): void => {
    if (formStartedRef.current) return
    formStartedRef.current = true
    trackEvent(funnelEventTypes.contactFormStart)
  }, [funnelEventTypes.contactFormStart])

  function handleSuccess(contactId: string): void {
    // Embudo: la respuesta fue 201. Emite `contact_form_success` [AC-6].
    trackEvent(funnelEventTypes.contactFormSuccess)
    const record = saveContactRecord(contactId)
    setSentRecord(record)
    setValues(emptyValues())
    setErrors({})
    setStatus('success')
    setStatusMessage(strings.statusSuccess)
    if (window.turnstile?.reset && widgetIdRef.current) {
      try {
        window.turnstile.reset(widgetIdRef.current)
      } catch {
        // ignorar
      }
    }
  }

  function handleApiError(
    httpStatus: number,
    body: (ApiErrorBody & ApiSuccessBody) | null,
  ): void {
    // Embudo: el envio fallo (4XX/5XX). Emite `contact_form_error` con el
    // codigo HTTP en `event_props` [AC-7].
    trackEvent(funnelEventTypes.contactFormError, { code: String(httpStatus) })
    if (httpStatus === 400) {
      const fieldErrors = mapPydanticErrors(body?.extra?.errors ?? [], strings)
      if (Object.keys(fieldErrors).length > 0) setErrors(fieldErrors)
      setStatus('error')
      setStatusMessage(body?.error || strings.statusInvalidFields)
      return
    }
    setStatus('error')
    setStatusMessage(errorMessageFor(httpStatus, strings))
  }

  function preflightCheck():
    | {
        ok: true
        data: ContactFormValues
        bypassSecret: string
        cfToken: string
      }
    | { ok: false } {
    const parsed = ContactFormSchema.safeParse(values)
    if (!parsed.success) {
      setErrors(getFieldErrors(parsed.error))
      setStatus('error')
      setStatusMessage(strings.statusInvalidFields)
      return { ok: false }
    }
    const bypassSecret = bypassTokenRef.current
    const cfToken = bypassSecret ? '' : turnstileToken
    if (!bypassSecret && !cfToken) {
      setStatus('error')
      setStatusMessage(strings.statusCaptchaMissing)
      return { ok: false }
    }
    return { ok: true, data: parsed.data, bypassSecret, cfToken }
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault()
    const pre = preflightCheck()
    if (!pre.ok) return

    setStatus('submitting')
    setStatusMessage(strings.submitting)

    // Embudo: el form se envia. Emite `contact_form_submit` [AC-6].
    trackEvent(funnelEventTypes.contactFormSubmit)

    // SPEC-202: enlaza el contacto con su journey via `session_id`. Ausente
    // si el visitante no tiene `cf_session` (rechazo el tracking) [AC-2].
    const payload = buildContactPayload(pre.data, {
      niche,
      cfToken: pre.cfToken,
      sessionId: readSessionId(),
    })
    const headers = buildHeaders(pre.bypassSecret)

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      const body = await parseJsonSafe(response)
      if (response.status === 201 && body?.contact_id) {
        handleSuccess(body.contact_id)
        return
      }
      handleApiError(response.status, body)
    } catch (_error) {
      // Error de red: no hay codigo HTTP. Emite `contact_form_error` con
      // `code: 'network'` para distinguirlo de los fallos 4XX/5XX [AC-7].
      trackEvent(funnelEventTypes.contactFormError, { code: 'network' })
      setStatus('error')
      setStatusMessage(strings.errorNetwork)
    }
  }

  function handleResend(): void {
    clearContactRecord()
    setSentRecord(null)
    setStatus('idle')
    setStatusMessage('')
    setTurnstileToken('')
    setErrors({})
  }

  // Card de confirmacion: el form esta oculto
  if (sentRecord) {
    const sentBody = strings.sentCardBody.replace(
      '{date}',
      formatSentDate(sentRecord.sentAt),
    )
    return (
      <div className="contact-form-wrapper" data-testid="contact-sent-card">
        <div className="contact-sent-card">
          <p className="contact-sent-card__title">{strings.sentCardTitle}</p>
          <p className="contact-sent-card__body">{sentBody}</p>
          <p className="contact-sent-card__ref">
            {strings.sentCardRefLabel}{' '}
            <code data-testid="contact-sent-id">{sentRecord.contactId}</code>
          </p>
          <button
            type="button"
            className="contact-sent-card__resend"
            data-testid="contact-resend-btn"
            onClick={handleResend}
          >
            {strings.sentCardResend}
          </button>
        </div>
      </div>
    )
  }

  const idFor = (key: string) => `${reactId}-${key}`

  return (
    <div className="contact-form-wrapper">
      <form
        className="contact-form"
        noValidate
        onSubmit={handleSubmit}
        onFocus={handleFormFocus}
        data-testid="contact-form"
        data-niche={niche}
      >
        <Field
          id={idFor('name')}
          label={strings.labelName}
          required
          name="name"
          autoComplete="name"
          value={values.name}
          error={errors.name}
          onChange={handleChange}
          onBlur={handleBlur}
        />

        <Field
          id={idFor('email')}
          label={strings.labelEmail}
          required
          type="email"
          name="email"
          autoComplete="email"
          value={values.email}
          error={errors.email}
          onChange={handleChange}
          onBlur={handleBlur}
        />

        <details className="form-optional">
          <summary>{strings.optionalSummary}</summary>

          <Field
            id={idFor('company')}
            label={strings.labelCompany}
            name="company"
            autoComplete="organization"
            value={values.company ?? ''}
            error={errors.company}
            onChange={handleChange}
            onBlur={handleBlur}
          />

          <Field
            id={idFor('role')}
            label={strings.labelRole}
            name="role"
            autoComplete="organization-title"
            value={values.role ?? ''}
            error={errors.role}
            onChange={handleChange}
            onBlur={handleBlur}
          />

          <div className="form-row">
            <label htmlFor={idFor('service_type')}>
              {strings.labelServiceType}
            </label>
            <select
              id={idFor('service_type')}
              name="service_type"
              value={values.service_type ?? ''}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-describedby={`${idFor('service_type')}-error`}
              aria-invalid={errors.service_type ? 'true' : undefined}
            >
              <option value="">{strings.serviceTypeUnset}</option>
              <option value="consulting">
                {strings.serviceTypeConsulting}
              </option>
              <option value="fulltime">{strings.serviceTypeFulltime}</option>
              <option value="contract">{strings.serviceTypeContract}</option>
              <option value="other">{strings.serviceTypeOther}</option>
            </select>
            {errors.service_type && (
              <small
                className="field-error"
                id={`${idFor('service_type')}-error`}
                data-testid="error-service_type"
              >
                {errors.service_type}
              </small>
            )}
          </div>

          <Field
            id={idFor('budget')}
            label={strings.labelBudget}
            name="budget"
            placeholder={strings.budgetPlaceholder}
            value={values.budget ?? ''}
            error={errors.budget}
            onChange={handleChange}
            onBlur={handleBlur}
          />

          <Field
            id={idFor('timeline')}
            label={strings.labelTimeline}
            name="timeline"
            placeholder={strings.timelinePlaceholder}
            value={values.timeline ?? ''}
            error={errors.timeline}
            onChange={handleChange}
            onBlur={handleBlur}
          />
        </details>

        <div className="form-row">
          <label htmlFor={idFor('message')}>
            {strings.labelMessage} <span aria-hidden>*</span>
          </label>
          <textarea
            id={idFor('message')}
            name="message"
            rows={6}
            required
            value={values.message}
            onChange={handleChange}
            onBlur={handleBlur}
            aria-describedby={`${idFor('message')}-error`}
            aria-invalid={errors.message ? 'true' : undefined}
          />
          {errors.message && (
            <small
              className="field-error"
              id={`${idFor('message')}-error`}
              data-testid="error-message"
            >
              {errors.message}
            </small>
          )}
        </div>

        {/* Turnstile widget: solo se renderiza si NO hay bypass de tests.
            La clase NO es `cf-turnstile`: esa clase dispara el render
            implicito de Turnstile (que necesita data-sitekey en el div y
            choca con el render explicito de mas abajo). El widget se monta
            con turnstile.render() explicito sobre este ref. */}
        {!bypassTokenRef.current && (
          <div
            className="turnstile-widget"
            ref={turnstileContainerRef}
            data-testid="turnstile-container"
          />
        )}

        <button
          type="submit"
          className="contact-submit"
          disabled={status === 'submitting'}
          data-testid="contact-submit"
        >
          <span className="submit-label">
            {status === 'submitting' ? strings.submitting : strings.submit}
          </span>
        </button>

        <p
          className="form-status"
          role="status"
          aria-live="polite"
          data-kind={status === 'idle' ? undefined : status}
          data-testid="contact-status"
        >
          {statusMessage}
        </p>
      </form>
    </div>
  )
}

// ------- Subcomponentes -------

interface FieldProps {
  id: string
  name: ContactFormFieldName
  label: string
  type?: string
  required?: boolean
  value: string
  error?: string
  autoComplete?: string
  placeholder?: string
  onChange: (e: ChangeEvent<HTMLInputElement>) => void
  onBlur: (e: FocusEvent<HTMLInputElement>) => void
}

function Field({
  id,
  name,
  label,
  type = 'text',
  required = false,
  value,
  error,
  autoComplete,
  placeholder,
  onChange,
  onBlur,
}: FieldProps) {
  return (
    <div className="form-row">
      <label htmlFor={id}>
        {label}
        {required && (
          <>
            {' '}
            <span aria-hidden>*</span>
          </>
        )}
      </label>
      <input
        id={id}
        name={name}
        type={type}
        value={value}
        required={required}
        autoComplete={autoComplete}
        placeholder={placeholder}
        onChange={onChange}
        onBlur={onBlur}
        aria-describedby={`${id}-error`}
        aria-invalid={error ? 'true' : undefined}
      />
      {error && (
        <small
          className="field-error"
          id={`${id}-error`}
          data-testid={`error-${name}`}
        >
          {error}
        </small>
      )}
    </div>
  )
}
