/**
 * @module contact-form-schema
 * @description Zod schema del form de contacto + helper para mapear errores
 *   Zod a un dict `<field, message>` que renderiza el componente React.
 *
 *   Reglas espejo del Pydantic backend (serverless/src/contact_form/schemas.py):
 *   - name: 2..200 chars
 *   - email: formato email valido + max 254
 *   - message: 10..5000 chars
 *   - company/role/budget/timeline: opcionales con max length
 *   - service_type: literal o vacio
 *   - session_id: opcional, 20..64 chars cuando esta presente (SPEC-202)
 */
import { z } from 'zod'

const SERVICE_TYPES = ['consulting', 'fulltime', 'contract', 'other'] as const

export const ContactFormSchema = z.object({
  name: z
    .string({ required_error: 'El nombre es obligatorio.' })
    .trim()
    .min(2, 'Minimo 2 caracteres.')
    .max(200, 'Maximo 200 caracteres.'),
  email: z
    .string({ required_error: 'El email es obligatorio.' })
    .trim()
    .min(1, 'El email es obligatorio.')
    .max(254, 'Maximo 254 caracteres.')
    .email('Email invalido. Revisa el formato.'),
  message: z
    .string({ required_error: 'El mensaje es obligatorio.' })
    .trim()
    .min(10, 'Minimo 10 caracteres.')
    .max(5000, 'Maximo 5000 caracteres.'),
  company: z
    .string()
    .trim()
    .max(200, 'Maximo 200 caracteres.')
    .optional()
    .or(z.literal('')),
  role: z
    .string()
    .trim()
    .max(100, 'Maximo 100 caracteres.')
    .optional()
    .or(z.literal('')),
  service_type: z
    .enum(SERVICE_TYPES, {
      errorMap: () => ({ message: 'Valor no permitido.' }),
    })
    .optional()
    .or(z.literal('')),
  budget: z
    .string()
    .trim()
    .max(100, 'Maximo 100 caracteres.')
    .optional()
    .or(z.literal('')),
  timeline: z
    .string()
    .trim()
    .max(100, 'Maximo 100 caracteres.')
    .optional()
    .or(z.literal('')),
})

export type ContactFormValues = z.infer<typeof ContactFormSchema>

export type ContactFormFieldName = keyof ContactFormValues

export type ContactFieldErrors = Partial<Record<ContactFormFieldName, string>>

/**
 * @schema SessionIdSchema
 * @description Validacion del `session_id` opcional del `POST /contact`
 *   (SPEC-202). Espejo del Pydantic backend: cuando esta presente debe medir
 *   20..64 chars; ausente es valido (visitante sin `cf_session`).
 *
 * @example
 *   SessionIdSchema.safeParse(undefined)            // success (ausente)
 *   SessionIdSchema.safeParse('a'.repeat(32))       // success
 *   SessionIdSchema.safeParse('short')              // error: min 20
 */
export const SessionIdSchema = z
  .string()
  .min(20, 'session_id invalido (minimo 20 caracteres).')
  .max(64, 'session_id invalido (maximo 64 caracteres).')
  .optional()

/**
 * @function getFieldErrors
 * @description Convierte un ZodError a un dict `{field: firstMessage}`.
 */
export function getFieldErrors(error: z.ZodError): ContactFieldErrors {
  const result: ContactFieldErrors = {}
  for (const issue of error.issues) {
    const field = issue.path[0]
    if (typeof field !== 'string') continue
    if (result[field as ContactFormFieldName]) continue
    result[field as ContactFormFieldName] = issue.message
  }
  return result
}

/**
 * @function emptyValues
 * @description Estado inicial del form (todos los campos vacios).
 */
export function emptyValues(): ContactFormValues {
  return {
    name: '',
    email: '',
    message: '',
    company: '',
    role: '',
    service_type: '',
    budget: '',
    timeline: '',
  }
}

/**
 * @type ContactPayloadContext
 * @description Contexto que `buildContactPayload` adjunta al body del POST,
 *   ademas de los campos del form: `niche`, token Turnstile y el
 *   `session_id` opcional de tracking (SPEC-202).
 */
export interface ContactPayloadContext {
  niche: string
  cfToken: string
  /** `session_id` de `localStorage.cf_session`. Ausente si no hay sesion. */
  sessionId?: string
}

/**
 * @function buildContactPayload
 * @description Funcion pura: arma el body del `POST /contact` desde los
 *   valores del form + el contexto. Recorta strings y descarta campos vacios.
 *   El `session_id` (SPEC-202) se agrega SOLO si viene un valor no vacio: un
 *   visitante sin `cf_session` produce un body sin la clave `session_id`.
 *
 * @param {ContactFormValues} data - Valores validados del formulario
 * @param {ContactPayloadContext} ctx - niche + token Turnstile + session_id
 *
 * @returns {Record<string, string>} Body listo para `JSON.stringify`
 *
 * @example
 *   buildContactPayload(values, { niche: 'generic', cfToken: 't' })
 *   // -> { niche: 'generic', cf_token: 't', name: '...', ... }  (sin session_id)
 *   buildContactPayload(values, {
 *     niche: 'generic', cfToken: 't', sessionId: 'a'.repeat(32),
 *   })
 *   // -> { ..., session_id: 'aaaa...' }
 */
export function buildContactPayload(
  data: ContactFormValues,
  ctx: ContactPayloadContext,
): Record<string, string> {
  const payload: Record<string, string> = {
    niche: ctx.niche,
    cf_token: ctx.cfToken,
  }
  for (const [key, raw] of Object.entries(data)) {
    const value = typeof raw === 'string' ? raw.trim() : ''
    if (value) payload[key] = value
  }
  // session_id opcional: nunca enviar la clave si no hay sesion (AC-2).
  if (ctx.sessionId) {
    payload.session_id = ctx.sessionId
  }
  return payload
}
