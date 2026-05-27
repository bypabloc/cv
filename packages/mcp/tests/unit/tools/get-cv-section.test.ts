/**
 * @description Tests para get_cv_section tool. Usa fakeProvider para no
 *   depender de @portfolio/content.
 */
import { describe, expect, it } from 'vitest'

import { definition, execute } from '../../../src/lib/tools/get-cv-section'
import { makeFakeProvider } from '../_fakes'

describe('get_cv_section.definition', () => {
  it('Given se inspecciona When leo el name Then es get_cv_section', () => {
    expect(definition.name).toBe('get_cv_section')
  })

  it('Given se inspecciona When leo el inputSchema Then exige section con enum', () => {
    expect(definition.inputSchema.required).toEqual(['section'])
    const section = definition.inputSchema.properties.section as {
      enum: string[]
    }
    expect(section.enum).toEqual([
      'about',
      'experience',
      'projects',
      'skills',
      'education',
      'contact',
    ])
  })
})

describe('get_cv_section.execute', () => {
  it('Given section=about When execute Then content[0] empieza con "# About"', async () => {
    const out = await execute({ section: 'about' }, makeFakeProvider())

    expect(out.content[0]!.type).toBe('text')
    expect(out.content[0]!.text.startsWith('# About\n')).toBe(true)
    expect(out.content[0]!.text).toContain('Lima, Peru')
  })

  it('Given section=experience When execute Then content incluye header Experience + roles del fake', async () => {
    const out = await execute({ section: 'experience' }, makeFakeProvider())

    expect(out.content[0]!.text.startsWith('# Experience\n')).toBe(true)
    expect(out.content[0]!.text).toContain('Frontend Architect @ Destacame')
    expect(out.content[0]!.text).toContain('Senior Engineer @ Acme Corp')
  })

  it('Given section=projects When execute Then content incluye header Projects + stacks', async () => {
    const out = await execute({ section: 'projects' }, makeFakeProvider())

    expect(out.content[0]!.text.startsWith('# Projects\n')).toBe(true)
    expect(out.content[0]!.text).toContain(
      '**Stack**: Astro, TypeScript, Cloudflare Pages',
    )
    expect(out.content[0]!.text).toContain(
      '**URL**: https://the-full-stack.com',
    )
  })

  it('Given section=skills When execute Then content incluye header Skills', async () => {
    const out = await execute({ section: 'skills' }, makeFakeProvider())

    expect(out.content[0]!.text.startsWith('# Skills\n')).toBe(true)
    expect(out.content[0]!.text).toContain('## Frontend')
    expect(out.content[0]!.text).toContain('- Vue 3')
  })

  it('Given section=education When execute Then content incluye header Education + degree', async () => {
    const out = await execute({ section: 'education' }, makeFakeProvider())

    expect(out.content[0]!.text.startsWith('# Education\n')).toBe(true)
    expect(out.content[0]!.text).toContain(
      '- **Computer Engineering**, Universidad Nacional (2010 - 2015)',
    )
    expect(out.content[0]!.text).toContain('- **AWS**, AWS (? - Present)')
  })

  it('Given section=contact When execute Then content incluye email del fake', async () => {
    const out = await execute({ section: 'contact' }, makeFakeProvider())

    expect(out.content[0]!.text.startsWith('# Contact\n')).toBe(true)
    expect(out.content[0]!.text).toContain('fake@example.com')
  })

  it('Given section invalido When execute Then throws con mensaje util', async () => {
    await expect(
      execute({ section: 'unknown' }, makeFakeProvider()),
    ).rejects.toThrow(/unknown section: unknown/)
  })

  it('Given section no string When execute Then throws', async () => {
    await expect(execute({ section: 42 }, makeFakeProvider())).rejects.toThrow(
      /unknown section/,
    )
  })

  it('Given args sin section When execute Then throws', async () => {
    await expect(execute({}, makeFakeProvider())).rejects.toThrow(
      /unknown section/,
    )
  })
})
