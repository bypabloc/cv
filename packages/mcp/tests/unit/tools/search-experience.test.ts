/**
 * @description Tests para search_experience tool.
 */
import { experiences } from '@portfolio/content'
import { describe, expect, it } from 'vitest'

import { definition, execute } from '../../../src/lib/tools/search-experience'

describe('search_experience.definition', () => {
  it('Given se inspecciona When leo el name Then es search_experience', () => {
    expect(definition.name).toBe('search_experience')
  })

  it('Given se inspecciona When leo el inputSchema Then exige keyword', () => {
    expect(definition.inputSchema.required).toEqual(['keyword'])
  })
})

describe('search_experience.execute', () => {
  it('Given keyword conocido When execute Then devuelve matches', async () => {
    const out = await execute({ keyword: 'Vue' })

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBeGreaterThan(0)
  })

  it('Given keyword no encontrado When execute Then devuelve array vacio', async () => {
    const out = await execute({ keyword: 'ZZZNOEXIST' })

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data).toEqual([])
  })

  it('Given keyword vacio When execute Then throws', async () => {
    await expect(execute({ keyword: '' })).rejects.toThrow(/non-empty/)
  })

  it('Given keyword whitespace When execute Then throws', async () => {
    await expect(execute({ keyword: '   ' })).rejects.toThrow(/non-empty/)
  })

  it('Given keyword no string When execute Then throws', async () => {
    await expect(execute({ keyword: 42 })).rejects.toThrow(/non-empty/)
  })

  it('Given keyword case-insensitive When execute Then match es independiente del case', async () => {
    const out1 = await execute({ keyword: 'PYTHON' })
    const out2 = await execute({ keyword: 'python' })

    const d1 = JSON.parse(out1.content[0]!.text) as unknown[]
    const d2 = JSON.parse(out2.content[0]!.text) as unknown[]
    expect(d1.length).toBe(d2.length)
  })

  it('Given se inspecciona When leo el shape del payload Then es {slug, role, company, start, end, achievements}', async () => {
    const out = await execute({ keyword: 'Vue' })

    const text = out.content[0]!.text
    const data = JSON.parse(text) as Record<string, unknown>[]
    expect(data.length).toBeGreaterThan(0)
    const first = data[0]!
    expect(Object.keys(first).sort()).toEqual([
      'achievements',
      'company',
      'end',
      'role',
      'slug',
      'start',
    ])
  })

  it('Given todos los matches When execute Then matches.length <= experiences.length', async () => {
    const out = await execute({ keyword: 'a' })

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBeLessThanOrEqual(experiences.length)
  })
})
