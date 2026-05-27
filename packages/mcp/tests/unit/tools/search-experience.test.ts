/**
 * @description Tests para search_experience tool. Usa fakeProvider para
 *   no depender de @portfolio/content.
 */
import { describe, expect, it } from 'vitest'

import { definition, execute } from '../../../src/lib/tools/search-experience'
import { FAKE_SNAPSHOT, makeFakeProvider } from '../_fakes'

describe('search_experience.definition', () => {
  it('Given se inspecciona When leo el name Then es search_experience', () => {
    expect(definition.name).toBe('search_experience')
  })

  it('Given se inspecciona When leo el inputSchema Then exige keyword', () => {
    expect(definition.inputSchema.required).toEqual(['keyword'])
  })
})

describe('search_experience.execute', () => {
  it('Given keyword=fintech When execute Then devuelve match con Destacame', async () => {
    const out = await execute({ keyword: 'fintech' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as { company: string }[]
    expect(data).toEqual([
      {
        slug: 'destacame-2024',
        role: 'Frontend Architect',
        company: 'Destacame',
        start: '2024-01',
        end: null,
        achievements: ['Reduced LCP from 3.2s to 1.4s on prod.'],
      },
    ])
  })

  it('Given keyword no encontrado When execute Then devuelve array vacio', async () => {
    const out = await execute({ keyword: 'ZZZNOEXIST' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data).toEqual([])
  })

  it('Given keyword vacio When execute Then throws', async () => {
    await expect(execute({ keyword: '' }, makeFakeProvider())).rejects.toThrow(
      /non-empty/,
    )
  })

  it('Given keyword whitespace When execute Then throws', async () => {
    await expect(
      execute({ keyword: '   ' }, makeFakeProvider()),
    ).rejects.toThrow(/non-empty/)
  })

  it('Given keyword no string When execute Then throws', async () => {
    await expect(execute({ keyword: 42 }, makeFakeProvider())).rejects.toThrow(
      /non-empty/,
    )
  })

  it('Given keyword case-insensitive When execute Then match es independiente del case', async () => {
    const out1 = await execute({ keyword: 'PYTHON' }, makeFakeProvider())
    const out2 = await execute({ keyword: 'python' }, makeFakeProvider())

    const d1 = JSON.parse(out1.content[0]!.text) as unknown[]
    const d2 = JSON.parse(out2.content[0]!.text) as unknown[]
    expect(d1.length).toBe(d2.length)
    expect(d1.length).toBe(1)
  })

  it('Given se inspecciona When leo el shape del payload Then es {slug, role, company, start, end, achievements}', async () => {
    const out = await execute({ keyword: 'fintech' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as Record<string, unknown>[]
    expect(Object.keys(data[0]!).sort()).toEqual([
      'achievements',
      'company',
      'end',
      'role',
      'slug',
      'start',
    ])
  })

  it('Given match en achievements When execute Then encuentra por substring de achievement', async () => {
    const out = await execute({ keyword: 'credit scoring' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as { slug: string }[]
    expect(data.length).toBe(1)
    expect(data[0]!.slug).toBe('acme-2022')
  })

  it('Given todos los matches When execute Then matches.length <= experiences.length', async () => {
    const out = await execute({ keyword: 'e' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBeLessThanOrEqual(FAKE_SNAPSHOT.experiences.length)
  })
})
