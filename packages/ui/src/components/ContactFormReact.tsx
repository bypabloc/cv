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
 */
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

interface ContactFormReactProps {
  apiEndpoint: string
  turnstileSitekey: string
  niche?: string
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

const ERROR_MESSAGES: Record<number | 'default', string> = {
  403: 'Captcha invalido. Recarga la pagina e intenta nuevamente.',
  429: 'Demasiados intentos. Espera unos minutos antes de reintentar.',
  default: 'Error del servidor. Intenta nuevamente en unos minutos.',
}

function buildPayload(
  data: ContactFormValues,
  ctx: { niche: string; cfToken: string },
): Record<string, string> {
  const payload: Record<string, string> = {
    niche: ctx.niche,
    cf_token: ctx.cfToken,
  }
  for (const [key, raw] of Object.entries(data)) {
    const value = typeof raw === 'string' ? raw.trim() : ''
    if (value) payload[key] = value
  }
  return payload
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
 * Mapea errores Pydantic del backend a `ContactFieldErrors`. Espejo del
 * humanizeError() del componente Astro original.
 */
function mapPydanticErrors(
  errors: NonNullable<NonNullable<ApiErrorBody['extra']>['errors']>,
): ContactFieldErrors {
  const result: ContactFieldErrors = {}
  for (const err of errors) {
    const field = [...err.loc]
      .reverse()
      .find((seg): seg is string => typeof seg === 'string')
    if (!field) continue
    if (result[field as ContactFormFieldName]) continue
    const min = err.ctx?.min_length
    const max = err.ctx?.max_length
    let msg: string
    switch (err.type) {
      case 'missing':
        msg = 'Este campo es obligatorio.'
        break
      case 'string_too_short':
        msg = `Minimo ${min ?? '?'} caracteres.`
        break
      case 'string_too_long':
        msg = `Maximo ${max ?? '?'} caracteres.`
        break
      case 'value_error':
      case 'value_error.email':
        msg = 'Email invalido. Revisa el formato.'
        break
      default:
        msg = err.msg || 'Valor invalido.'
    }
    result[field as ContactFormFieldName] = msg
  }
  return result
}

export default function ContactFormReact({
  apiEndpoint,
  turnstileSitekey,
  niche = 'generic',
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
          setStatusMessage('Error cargando el captcha. Recarga la pagina.')
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
  }, [sentRecord, turnstileSitekey])

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
          next[field] = result.error.issues[0]?.message ?? 'Valor invalido.'
        }
        return next
      })
    },
    [],
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

  function handleSuccess(contactId: string): void {
    const record = saveContactRecord(contactId)
    setSentRecord(record)
    setValues(emptyValues())
    setErrors({})
    setStatus('success')
    setStatusMessage('Mensaje enviado. Te respondere en menos de 24h.')
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
    if (httpStatus === 400) {
      const fieldErrors = mapPydanticErrors(body?.extra?.errors ?? [])
      if (Object.keys(fieldErrors).length > 0) setErrors(fieldErrors)
      setStatus('error')
      setStatusMessage(
        body?.error || 'Hay datos invalidos. Revisa los campos marcados.',
      )
      return
    }
    setStatus('error')
    setStatusMessage(ERROR_MESSAGES[httpStatus] ?? ERROR_MESSAGES.default)
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
      setStatusMessage('Hay datos invalidos. Revisa los campos marcados.')
      return { ok: false }
    }
    const bypassSecret = bypassTokenRef.current
    const cfToken = bypassSecret ? '' : turnstileToken
    if (!bypassSecret && !cfToken) {
      setStatus('error')
      setStatusMessage('Por favor completa el captcha antes de enviar.')
      return { ok: false }
    }
    return { ok: true, data: parsed.data, bypassSecret, cfToken }
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault()
    const pre = preflightCheck()
    if (!pre.ok) return

    setStatus('submitting')
    setStatusMessage('Enviando...')

    const payload = buildPayload(pre.data, { niche, cfToken: pre.cfToken })
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
      setStatus('error')
      setStatusMessage('Error de red. Verifica tu conexion y reintenta.')
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
    return (
      <div className="contact-form-wrapper" data-testid="contact-sent-card">
        <div className="contact-sent-card">
          <p className="contact-sent-card__title">Mensaje enviado</p>
          <p className="contact-sent-card__body">
            Ya enviaste un mensaje el {formatSentDate(sentRecord.sentAt)}. Te
            respondere en menos de 24h.
          </p>
          <p className="contact-sent-card__ref">
            Ref:{' '}
            <code data-testid="contact-sent-id">{sentRecord.contactId}</code>
          </p>
          <button
            type="button"
            className="contact-sent-card__resend"
            data-testid="contact-resend-btn"
            onClick={handleResend}
          >
            Enviar otro mensaje
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
        data-testid="contact-form"
        data-niche={niche}
      >
        <Field
          id={idFor('name')}
          label="Nombre"
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
          label="Email"
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
          <summary>Datos opcionales (para conocerte mejor)</summary>

          <Field
            id={idFor('company')}
            label="Empresa"
            name="company"
            autoComplete="organization"
            value={values.company ?? ''}
            error={errors.company}
            onChange={handleChange}
            onBlur={handleBlur}
          />

          <Field
            id={idFor('role')}
            label="Cargo / Rol"
            name="role"
            autoComplete="organization-title"
            value={values.role ?? ''}
            error={errors.role}
            onChange={handleChange}
            onBlur={handleBlur}
          />

          <div className="form-row">
            <label htmlFor={idFor('service_type')}>Tipo de servicio</label>
            <select
              id={idFor('service_type')}
              name="service_type"
              value={values.service_type ?? ''}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-describedby={`${idFor('service_type')}-error`}
              aria-invalid={errors.service_type ? 'true' : undefined}
            >
              <option value="">(sin especificar)</option>
              <option value="consulting">Consultoria</option>
              <option value="fulltime">Full-time</option>
              <option value="contract">Contrato / freelance</option>
              <option value="other">Otro</option>
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
            label="Presupuesto"
            name="budget"
            placeholder="Ej: USD 5k-15k / mes"
            value={values.budget ?? ''}
            error={errors.budget}
            onChange={handleChange}
            onBlur={handleBlur}
          />

          <Field
            id={idFor('timeline')}
            label="Timeline"
            name="timeline"
            placeholder="Ej: empieza en 2 semanas"
            value={values.timeline ?? ''}
            error={errors.timeline}
            onChange={handleChange}
            onBlur={handleBlur}
          />
        </details>

        <div className="form-row">
          <label htmlFor={idFor('message')}>
            Mensaje <span aria-hidden>*</span>
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
            {status === 'submitting' ? 'Enviando...' : 'Enviar'}
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
