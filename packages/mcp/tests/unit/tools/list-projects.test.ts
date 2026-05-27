/**
 * @description Tests para list_projects tool. Usa fakeProvider para no
 *   depender de @portfolio/content.
 */
import { describe, expect, it } from 'vitest'

import { definition, execute } from '../../../src/lib/tools/list-projects'
import { FAKE_SNAPSHOT, makeFakeProvider } from '../_fakes'

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
  it('Given sin filter When execute Then devuelve TODOS los proyectos del provider', async () => {
    const out = await execute({}, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBe(FAKE_SNAPSHOT.projects.length)
  })

  it('Given tech_stack=Astro When execute Then solo proyectos con Astro en stack', async () => {
    const out = await execute({ tech_stack: 'Astro' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as { stack: string[] }[]
    expect(data).toEqual([
      {
        slug: 'portfolio',
        name: 'the-full-stack.com',
        summary: 'Personal portfolio with 6 niches.',
        stack: ['Astro', 'TypeScript', 'Cloudflare Pages'],
        url: 'https://the-full-stack.com',
      },
    ])
  })

  it('Given tech_stack=XYZNOEXIST When execute Then devuelve array vacio', async () => {
    const out = await execute({ tech_stack: 'XYZNOEXIST' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data).toEqual([])
  })

  it('Given tech_stack vacio When execute Then ignora el filter (devuelve todos)', async () => {
    const out = await execute({ tech_stack: '   ' }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBe(FAKE_SNAPSHOT.projects.length)
  })

  it('Given tech_stack no string When execute Then ignora el filter (devuelve todos)', async () => {
    const out = await execute({ tech_stack: 42 }, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as unknown[]
    expect(data.length).toBe(FAKE_SNAPSHOT.projects.length)
  })

  it('Given se inspecciona When leo el shape del payload Then es {slug, name, summary, stack, url}', async () => {
    const out = await execute({}, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as Record<string, unknown>[]
    expect(Object.keys(data[0]!).sort()).toEqual([
      'name',
      'slug',
      'stack',
      'summary',
      'url',
    ])
  })

  it('Given proyecto sin URL When execute Then payload tiene url=null', async () => {
    const out = await execute({}, makeFakeProvider())

    const data = JSON.parse(out.content[0]!.text) as {
      slug: string
      url: string | null
    }[]
    const devtools = data.find((p) => p.slug === 'devtools-cli')!
    expect(devtools.url).toBe(null)
  })
})
