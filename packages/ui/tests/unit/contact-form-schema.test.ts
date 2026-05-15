/**
 * @description Tests para contact-form-schema (Zod): validacion + mapeo de
 *   errores. Refleja las mismas reglas del Pydantic backend.
 */
import { describe, expect, it } from 'vitest'
import {
  ContactFormSchema,
  emptyValues,
  getFieldErrors,
} from '../../src/lib/contact-form-schema'

describe('ContactFormSchema', () => {
  it('Given valores validos minimos When parse Then success', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: 'Pablo',
      email: 'pacg1991@gmail.com',
      message: 'Hola, tengo un proyecto interesante para discutir.',
    })
    expect(result.success).toBe(true)
  })

  it('Given name vacio When parse Then error en name', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: '',
      email: 'a@b.com',
      message: 'Mensaje suficientemente largo para pasar.',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      const fieldErrors = getFieldErrors(result.error)
      expect(fieldErrors.name).toBe('Minimo 2 caracteres.')
    }
  })

  it('Given email invalido When parse Then error en email', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: 'Pablo',
      email: 'no-es-email',
      message: 'Mensaje suficientemente largo para pasar.',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      const fieldErrors = getFieldErrors(result.error)
      expect(fieldErrors.email).toBe('Email invalido. Revisa el formato.')
    }
  })

  it('Given message muy corto When parse Then error de min 10', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: 'Pablo',
      email: 'a@b.com',
      message: 'corto',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      const fieldErrors = getFieldErrors(result.error)
      expect(fieldErrors.message).toBe('Minimo 10 caracteres.')
    }
  })

  it('Given message excede 5000 chars When parse Then error de max', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: 'Pablo',
      email: 'a@b.com',
      message: 'x'.repeat(5001),
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      const fieldErrors = getFieldErrors(result.error)
      expect(fieldErrors.message).toBe('Maximo 5000 caracteres.')
    }
  })

  it('Given service_type vacio When parse Then success (campo opcional)', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: 'Pablo',
      email: 'a@b.com',
      message: 'Mensaje suficientemente largo para pasar.',
      service_type: '',
    })
    expect(result.success).toBe(true)
  })

  it('Given service_type valido When parse Then success', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: 'Pablo',
      email: 'a@b.com',
      message: 'Mensaje suficientemente largo para pasar.',
      service_type: 'consulting',
    })
    expect(result.success).toBe(true)
  })

  it('Given service_type invalido When parse Then error', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: 'Pablo',
      email: 'a@b.com',
      message: 'Mensaje suficientemente largo para pasar.',
      service_type: 'enterprise',
    })
    expect(result.success).toBe(false)
  })

  it('Given multiples errores When getFieldErrors Then retorna primero por campo', () => {
    const result = ContactFormSchema.safeParse({
      ...emptyValues(),
      name: '',
      email: 'no-es-email',
      message: 'corto',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      const fieldErrors = getFieldErrors(result.error)
      expect(fieldErrors.name).toBe('Minimo 2 caracteres.')
      expect(fieldErrors.email).toBe('Email invalido. Revisa el formato.')
      expect(fieldErrors.message).toBe('Minimo 10 caracteres.')
    }
  })
})

describe('emptyValues', () => {
  it('When call Then returns all fields empty strings', () => {
    const v = emptyValues()
    expect(v).toEqual({
      name: '',
      email: '',
      message: '',
      company: '',
      role: '',
      service_type: '',
      budget: '',
      timeline: '',
    })
  })
})
