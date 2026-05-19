/**
 * @description Tests para loadI18nFile. Cubre AC-3 (Zod error con path del
 *   archivo) y la resolucion de la clave del glob con/sin prefijo `./`.
 */
import { describe, expect, it } from 'vitest'
import { z } from 'zod'
import { loadI18nFile } from '../../src/lib/load-i18n-file'

const TestSchema = z.object({
  title: z.string().min(1),
  count: z.number().int(),
})

describe('loadI18nFile', () => {
  it('Given a valid module When loaded Then returns the parsed object', () => {
    const modules = {
      './foo.es.yaml': { default: { title: 'Hola', count: 3 } },
    }
    const result = loadI18nFile('./foo.es.yaml', modules, TestSchema)
    expect(result).toEqual({ title: 'Hola', count: 3 })
  })

  it('Given a path without leading ./ When loaded Then resolves the key anyway', () => {
    const modules = {
      './bar.en.yaml': { default: { title: 'Hi', count: 1 } },
    }
    const result = loadI18nFile('bar.en.yaml', modules, TestSchema)
    expect(result).toEqual({ title: 'Hi', count: 1 })
  })

  it('Given a module without default export When loaded Then throws with the key', () => {
    const modules = {
      './broken.yaml': { notDefault: { title: 'x', count: 1 } },
    }
    expect(() =>
      loadI18nFile('./broken.yaml', modules, TestSchema),
    ).toThrowError(/broken\.yaml.*default export/s)
  })

  it('Given a module that fails Zod When loaded Then throws with the path and Zod message', () => {
    const modules = {
      './invalid.yaml': { default: { title: '', count: 'NaN' } },
    }
    expect(() =>
      loadI18nFile('./invalid.yaml', modules, TestSchema),
    ).toThrowError(/invalid\.yaml.*validacion Zod/s)
  })

  it('Given a missing path When loaded Then throws listing available keys', () => {
    const modules = {
      './present.yaml': { default: { title: 'ok', count: 1 } },
    }
    expect(() =>
      loadI18nFile('./absent.yaml', modules, TestSchema),
    ).toThrowError(/no se encontro "\.\/absent\.yaml"/)
  })
})
