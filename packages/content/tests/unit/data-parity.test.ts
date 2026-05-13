/**
 * @description Tests de paridad: cada entidad expuesta por el barrel del
 *   package debe matchear el snapshot baseline guardado en
 *   `tests/fixtures/baseline/<entity>.json`. Cubre AC-1 y AC-4 del
 *   refactor YAML.
 *
 *   El baseline se genero a partir de los .ts monoliticos pre-refactor
 *   (ver docs/specs/refactor-cv-data-yaml.md). Sirve como regression test
 *   permanente: si alguien edita un YAML por error y rompe el shape o
 *   pierde contenido, el snapshot atrapa el drift.
 *
 *   Si esto falla, una de dos:
 *     (a) hay drift de contenido (un YAML se rompio sin querer)
 *     (b) un cambio de data es deliberado y hay que actualizar el baseline
 *
 *   Para regenerar el baseline (cambio deliberado):
 *     pnpm dlx tsx tmp/baseline-gen.mjs    # genera tmp/cv-baseline/*.json
 *     cp tmp/cv-baseline/*.json packages/content/tests/fixtures/baseline/
 *
 *   Comparacion: arrays ordenados por slug en ambos lados (loadYamlEntries
 *   sortea por slug ascendente).
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  awards,
  certificates,
  education,
  experiences,
  languages,
  profile,
  projects,
  publications,
  references,
  skills,
} from '../../src/index'

const baselineDir = resolve(__dirname, '../fixtures/baseline')

function loadBaseline<T>(entity: string): T {
  const path = resolve(baselineDir, `${entity}.json`)
  return JSON.parse(readFileSync(path, 'utf8')) as T
}

interface WithSlug {
  slug: string
}

/** Ordena por slug — para comparar sets independientemente del orden source. */
function bySlug<T extends WithSlug>(arr: readonly T[]): T[] {
  return [...arr].sort((a, b) => a.slug.localeCompare(b.slug))
}

describe('data parity (post-refactor vs baseline)', () => {
  it('Given profile When importing Then matches baseline', () => {
    const baseline = loadBaseline<typeof profile>('profile')
    expect(profile).toEqual(baseline)
  })

  it('Given experiences When importing Then matches baseline (sorted by slug)', () => {
    const baseline = loadBaseline<(typeof experiences)[number][]>('experiences')
    expect(bySlug(experiences)).toEqual(bySlug(baseline))
  })

  it('Given projects When importing Then matches baseline (sorted by slug)', () => {
    const baseline = loadBaseline<(typeof projects)[number][]>('projects')
    expect(bySlug(projects)).toEqual(bySlug(baseline))
  })

  it('Given skills When importing Then matches baseline (sorted by slug)', () => {
    const baseline = loadBaseline<(typeof skills)[number][]>('skills')
    expect(bySlug(skills)).toEqual(bySlug(baseline))
  })

  it('Given certificates When importing Then matches baseline (sorted by slug)', () => {
    const baseline =
      loadBaseline<(typeof certificates)[number][]>('certificates')
    expect(bySlug(certificates)).toEqual(bySlug(baseline))
  })

  it('Given publications When importing Then matches baseline (sorted by slug)', () => {
    const baseline =
      loadBaseline<(typeof publications)[number][]>('publications')
    expect(bySlug(publications)).toEqual(bySlug(baseline))
  })

  it('Given awards When importing Then matches baseline (sorted by slug)', () => {
    const baseline = loadBaseline<(typeof awards)[number][]>('awards')
    expect(bySlug(awards)).toEqual(bySlug(baseline))
  })

  it('Given education When importing Then matches baseline (sorted by slug)', () => {
    const baseline = loadBaseline<(typeof education)[number][]>('education')
    expect(bySlug(education)).toEqual(bySlug(baseline))
  })

  it('Given references When importing Then matches baseline (sorted by slug)', () => {
    const baseline = loadBaseline<(typeof references)[number][]>('references')
    expect(bySlug(references)).toEqual(bySlug(baseline))
  })

  it('Given languages When importing Then matches baseline (sorted by name.en)', () => {
    const baseline = loadBaseline<(typeof languages)[number][]>('languages')
    // languages no tienen slug; comparamos sets ordenados por name.en
    const byName = <T extends { name: { en: string } }>(
      arr: readonly T[],
    ): T[] => [...arr].sort((a, b) => a.name.en.localeCompare(b.name.en))
    expect(byName(languages)).toEqual(byName(baseline))
  })
})
