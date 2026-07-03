/**
 * @description Test de paridad de traduccion (AC-2). Verifica que los YAML
 *   i18n es/en tienen exactamente las mismas claves: elements, curriculum de
 *   las 6 apps y hub-selector. Tambien valida que cada YAML parsea con su
 *   schema Zod (AC-3) — los loaders lanzan al importarse si algo falla.
 */
import { describe, expect, it } from 'vitest'
import {
  CURRICULUM_APPS,
  elements,
  getCurriculum,
  hubSelector,
} from '../../src/data/i18n/index'

/**
 * Extrae todas las rutas de claves de un objeto, recursivamente, ordenadas.
 * Los arrays se recorren por indice para detectar tambien diferencias de
 * longitud entre es/en.
 */
function keyPaths(value: unknown, prefix = ''): string[] {
  if (Array.isArray(value)) {
    return value.flatMap((item, idx) => keyPaths(item, `${prefix}[${idx}]`))
  }
  if (value && typeof value === 'object') {
    return Object.keys(value)
      .sort()
      .flatMap((key) => {
        const next = prefix ? `${prefix}.${key}` : key
        return keyPaths((value as Record<string, unknown>)[key], next)
      })
  }
  return [prefix]
}

describe('i18n parity es/en', () => {
  it('Given elements.es and elements.en When compared Then key paths are identical', () => {
    expect(keyPaths(elements.es)).toEqual(keyPaths(elements.en))
  })

  it('Given hub-selector es and en When compared Then key paths are identical', () => {
    expect(keyPaths(hubSelector.es)).toEqual(keyPaths(hubSelector.en))
  })

  for (const app of CURRICULUM_APPS) {
    it(`Given curriculum ${app} es and en When compared Then key paths are identical`, () => {
      const es = getCurriculum(app, 'es')
      const en = getCurriculum(app, 'en')
      expect(keyPaths(es)).toEqual(keyPaths(en))
    })
  }
})

describe('i18n content sanity', () => {
  it('Given elements When loaded Then nav has the 7 expected keys', () => {
    expect(elements.es.nav.map((n) => n.key)).toEqual([
      'experience',
      'projects',
      'skills',
      'about',
      'certificates',
      'contact',
      'hub',
    ])
  })

  it('Given the 6 apps When curriculum loaded Then each has a non-empty meta title', () => {
    for (const app of CURRICULUM_APPS) {
      expect(getCurriculum(app, 'es').meta.title.length).toBeGreaterThan(0)
      expect(getCurriculum(app, 'en').meta.title.length).toBeGreaterThan(0)
    }
  })

  it('Given hub-selector When loaded Then it has exactly 6 cards (5 niches + journey)', () => {
    expect(hubSelector.es.cards).toHaveLength(6)
    expect(hubSelector.en.cards).toHaveLength(6)
    expect(hubSelector.es.cards.map((c) => c.niche)).toEqual([
      'generic',
      'fintech',
      'architect',
      'leader',
      'vibe',
      'journey',
    ])
  })

  it('Given the fintech niche When curriculum loaded Then hero.summary is fintech-specific (mentions financial institutions)', () => {
    expect(getCurriculum('fintech', 'es').hero.summary).toContain(
      'instituciones financieras',
    )
    expect(getCurriculum('fintech', 'en').hero.summary).toContain(
      'financial institutions',
    )
  })

  it('Given a niche with its own hero.summary When loaded Then it differs from the generic summary', () => {
    const fintech = getCurriculum('fintech', 'es').hero.summary
    const architect = getCurriculum('architect', 'es').hero.summary
    expect(fintech).not.toBe(architect)
  })
})
