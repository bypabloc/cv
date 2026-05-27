/**
 * @description Tests para list_projects tool.
 */
import { projects } from '@portfolio/content'
import { describe, expect, it } from 'vitest'

import { definition, execute } from '../../../src/lib/tools/list-projects'

describe('list_projects.definition', () => {
  it('Given se inspecciona When leo el name Then es list_projects', () => {
    expect(definition.name).toBe('list_projects')
  })

  it('Given se inspecciona When leo el inputSchema Then tech_stack es opcional', () => {
    expect(definition.inputSchema.required).toBeUndefined()
    expect(definition.inputSchema.properties.tech_stack).toBeDefined()
  })
})

describe('list_projects.execute', () => {
  it('Given sin filter When execute Then devuelve TODOS los proyectos', async () => {
    const out = await execute({})

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBe(projects.length)
  })

  it('Given tech_stack=Astro When execute Then todos tienen Astro en stack', async () => {
    const out = await execute({ tech_stack: 'Astro' })

    const data = JSON.parse(out.content[0]!.text) as {
      stack: string[]
    }[]
    expect(data.length).toBeGreaterThan(0)
    for (const project of data) {
      const stackLower = project.stack.map((s) => s.toLowerCase()).join(' ')
      expect(stackLower).toContain('astro')
    }
  })

  it('Given tech_stack=XYZNOEXIST When execute Then devuelve array vacio', async () => {
    const out = await execute({ tech_stack: 'XYZNOEXIST' })

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data).toEqual([])
  })

  it('Given tech_stack vacio When execute Then ignora el filter (devuelve todos)', async () => {
    const out = await execute({ tech_stack: '   ' })

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBe(projects.length)
  })

  it('Given tech_stack no string When execute Then ignora el filter (devuelve todos)', async () => {
    const out = await execute({ tech_stack: 42 })

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBe(projects.length)
  })

  it('Given se inspecciona When leo el shape del payload Then es {slug, name, summary, stack, url}', async () => {
    const out = await execute({})

    const data = JSON.parse(out.content[0]!.text) as Record<string, unknown>[]
    expect(data.length).toBeGreaterThan(0)
    expect(Object.keys(data[0]!).sort()).toEqual([
      'name',
      'slug',
      'stack',
      'summary',
      'url',
    ])
  })
})
