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
