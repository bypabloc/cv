/**
 * @description Tests para contact-form-schema (Zod): validacion + mapeo de
 *   errores. Refleja las mismas reglas del Pydantic backend.
 */
import { describe, expect, it } from 'vitest'
import { z } from 'zod'
import {
  buildContactPayload,
  ContactFormSchema,
  emptyValues,
  getFieldErrors,
  SessionIdSchema,
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

describe('getFieldErrors', () => {
  it('Given issue con path[0] no-string When mapeo Then se ignora', () => {
    // ZodError con path no-string (e.g. raiz). Branch coverage de
    // contact-form-schema.ts L80 (`if (typeof field !== 'string') continue`).
    const error = z.ZodError.create([
      {
        code: 'custom',
        path: [],
        message: 'error en raiz',
      },
    ])
    const result = getFieldErrors(error)
    expect(result).toEqual({})
  })

  it('Given dos issues en mismo campo When mapeo Then se queda el primer mensaje', () => {
    // Branch coverage de L81 (`if (result[field]) continue`).
    const error = z.ZodError.create([
      {
        code: 'custom',
        path: ['email'],
        message: 'primer error',
      },
      {
        code: 'custom',
        path: ['email'],
        message: 'segundo error',
      },
    ])
    const result = getFieldErrors(error)
    expect(result.email).toBe('primer error')
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

describe('SessionIdSchema (SPEC-202)', () => {
  it('Given session_id ausente When parse Then success (es opcional)', () => {
    const result = SessionIdSchema.safeParse(undefined)
    expect(result.success).toBe(true)
  })

  it('Given session_id de 32 chars When parse Then success', () => {
    const result = SessionIdSchema.safeParse('a'.repeat(32))
    expect(result.success).toBe(true)
  })

  it('Given session_id en el limite de 20 chars When parse Then success', () => {
    const result = SessionIdSchema.safeParse('a'.repeat(20))
    expect(result.success).toBe(true)
  })

  it('Given session_id en el limite de 64 chars When parse Then success', () => {
    const result = SessionIdSchema.safeParse('a'.repeat(64))
    expect(result.success).toBe(true)
  })

  it('Given session_id de 19 chars When parse Then error de minimo', () => {
    const result = SessionIdSchema.safeParse('a'.repeat(19))
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0]?.message).toBe(
        'session_id invalido (minimo 20 caracteres).',
      )
    }
  })

  it('Given session_id de 65 chars When parse Then error de maximo', () => {
    const result = SessionIdSchema.safeParse('a'.repeat(65))
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0]?.message).toBe(
        'session_id invalido (maximo 64 caracteres).',
      )
    }
  })
})

describe('buildContactPayload (SPEC-202)', () => {
  const baseValues = {
    ...emptyValues(),
    name: 'Pablo',
    email: 'pacg1991@gmail.com',
    message: 'Mensaje suficientemente largo para pasar.',
  }

  it('Given sessionId presente When build Then el payload incluye session_id [AC-1]', () => {
    // Arrange
    const sessionId = 'a'.repeat(32)

    // Act
    const payload = buildContactPayload(baseValues, {
      niche: 'generic',
      cfToken: 'tok',
      sessionId,
    })

    // Assert
    expect(payload.session_id).toBe(sessionId)
    expect(payload.niche).toBe('generic')
    expect(payload.cf_token).toBe('tok')
    expect(payload.name).toBe('Pablo')
  })

  it('Given sessionId ausente When build Then el payload NO tiene la clave session_id [AC-2]', () => {
    // Act
    const payload = buildContactPayload(baseValues, {
      niche: 'generic',
      cfToken: 'tok',
    })

    // Assert
    expect('session_id' in payload).toBe(false)
  })

  it('Given sessionId string vacio When build Then el payload NO tiene la clave session_id [AC-2]', () => {
    // Act
    const payload = buildContactPayload(baseValues, {
      niche: 'generic',
      cfToken: 'tok',
      sessionId: '',
    })

    // Assert
    expect('session_id' in payload).toBe(false)
  })

  it('Given campos opcionales vacios When build Then se descartan del payload', () => {
    // Act
    const payload = buildContactPayload(baseValues, {
      niche: 'fintech',
      cfToken: 'tok',
    })

    // Assert
    expect('company' in payload).toBe(false)
    expect('role' in payload).toBe(false)
    expect('service_type' in payload).toBe(false)
  })

  it('Given campos con espacios When build Then se recortan los valores', () => {
    // Act
    const payload = buildContactPayload(
      { ...baseValues, company: '  Acme  ' },
      { niche: 'generic', cfToken: 'tok', sessionId: 'a'.repeat(20) },
    )

    // Assert
    expect(payload.company).toBe('Acme')
  })
})
