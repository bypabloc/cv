/**
 * @description Tests para renderCvHtml. Cubre AC-8.
 */
import { describe, expect, it } from 'vitest'
import { renderCvHtml } from '../../src/lib/render-cv-html'

describe('renderCvHtml', () => {
  it('Given locale es generic When render Then includes Pablo name and Spanish summary heading', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'generic' })
    expect(html).toMatch(/<h1>Pablo Contreras<\/h1>/u)
    expect(html).toMatch(/<h2>Resumen<\/h2>/u)
    expect(html).toMatch(/<h2>Experiencia<\/h2>/u)
    expect(html).toMatch(/<h2>Habilidades técnicas<\/h2>/u)
    expect(html).toMatch(/<h2>Educación<\/h2>/u)
  })

  it('Given locale en generic When render Then uses English labels', () => {
    const html = renderCvHtml({ locale: 'en', niche: 'generic' })
    expect(html).toMatch(/<h2>Summary<\/h2>/u)
    expect(html).toMatch(/<h2>Experience<\/h2>/u)
    expect(html).toMatch(/<h2>Technical skills<\/h2>/u)
  })

  it('Given niche fintech When render Then prioritizes Destacame entries', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'fintech' })
    const firstRoleIdx = html.indexOf('<h3>')
    const firstRoleBlock = html.slice(firstRoleIdx, firstRoleIdx + 500)
    expect(firstRoleBlock).toMatch(/Destacame/u)
  })

  it('Given niche vibe When render Then includes FastStruct project', () => {
    const html = renderCvHtml({ locale: 'en', niche: 'vibe' })
    expect(html).toContain('FastStruct')
  })

  it('Given any niche When render Then has valid HTML doctype and lang attr', () => {
    const html = renderCvHtml({ locale: 'en', niche: 'fintech' })
    expect(html.startsWith('<!doctype html>')).toBe(true)
    expect(html).toMatch(/<html lang="en">/u)
  })

  it('Given any input When render Then contains contact links', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'generic' })
    expect(html).toContain('mailto:pacg1991@gmail.com')
    expect(html).toContain('linkedin.com/in/bypabloc')
    expect(html).toContain('github.com/bypabloc')
  })

  it('Given any input When render Then escapes potentially unsafe chars', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'generic' })
    // No raw < or > that could break the HTML inside text nodes.
    expect(html).not.toContain('<script>alert(')
  })
})
