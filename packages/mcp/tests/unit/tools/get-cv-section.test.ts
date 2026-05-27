/**
 * @description Tests para get_cv_section tool.
 */
import { describe, expect, it } from 'vitest'

import { definition, execute } from '../../../src/lib/tools/get-cv-section'

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
    const out = await execute({ section: 'about' })

    expect(out.content[0]!.type).toBe('text')
    expect(out.content[0]!.text.startsWith('# About\n')).toBe(true)
  })

  it('Given section=experience When execute Then content incluye header Experience', async () => {
    const out = await execute({ section: 'experience' })

    expect(out.content[0]!.text.startsWith('# Experience\n')).toBe(true)
    expect(out.content[0]!.text).toContain('## ')
  })

  it('Given section=projects When execute Then content incluye header Projects', async () => {
    const out = await execute({ section: 'projects' })

    expect(out.content[0]!.text.startsWith('# Projects\n')).toBe(true)
    expect(out.content[0]!.text).toContain('**Stack**')
  })

  it('Given section=skills When execute Then content incluye header Skills', async () => {
    const out = await execute({ section: 'skills' })

    expect(out.content[0]!.text.startsWith('# Skills\n')).toBe(true)
  })

  it('Given section=education When execute Then content incluye header Education', async () => {
    const out = await execute({ section: 'education' })

    expect(out.content[0]!.text.startsWith('# Education\n')).toBe(true)
  })

  it('Given section=contact When execute Then content incluye email', async () => {
    const out = await execute({ section: 'contact' })

    expect(out.content[0]!.text.startsWith('# Contact\n')).toBe(true)
    expect(out.content[0]!.text).toContain('Email')
  })

  it('Given section invalido When execute Then throws con mensaje util', async () => {
    await expect(execute({ section: 'unknown' })).rejects.toThrow(
      /unknown section: unknown/,
    )
  })

  it('Given section no string When execute Then throws', async () => {
    await expect(execute({ section: 42 })).rejects.toThrow(/unknown section/)
  })

  it('Given args sin section When execute Then throws', async () => {
    await expect(execute({})).rejects.toThrow(/unknown section/)
  })
})
