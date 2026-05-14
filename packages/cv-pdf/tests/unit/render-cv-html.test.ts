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

describe('renderCvHtml CV filters layer [AC-9, AC-17, AC-18]', () => {
  it('Given enableFilters=false (default) Then NO filter bar in HTML', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'generic' })
    expect(html).not.toContain('data-filter-bar')
    expect(html).not.toContain('cv-filters.js')
  })

  it('Given enableFilters=true Then filter bar is present and hidden by default [AC-18]', () => {
    const html = renderCvHtml({
      locale: 'es',
      niche: 'generic',
      enableFilters: true,
    })
    expect(html).toContain('data-filter-bar')
    expect(html).toMatch(/data-filter-bar[^>]*hidden/u)
  })

  it('Given enableFilters=true Then references cv-filters.js script', () => {
    const html = renderCvHtml({
      locale: 'es',
      niche: 'generic',
      enableFilters: true,
    })
    expect(html).toContain('<script src="/cv-filters.js" defer></script>')
  })

  it('Given any render Then experiences are wrapped in data-filter-section="experience"', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'generic' })
    expect(html).toContain('data-filter-section="experience"')
  })

  it('Given any render Then projects are wrapped in data-filter-section="project"', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'vibe' })
    expect(html).toContain('data-filter-section="project"')
  })

  it('Given any render Then each experience article has data-tech, data-seniority, data-start [AC-17]', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'fintech' })
    expect(html).toMatch(/<article data-filterable[^>]*data-tech="/u)
    expect(html).toMatch(/<article data-filterable[^>]*data-seniority="/u)
    expect(html).toMatch(/<article data-filterable[^>]*data-start="/u)
  })

  it('Given any render Then each project article has data-tech, data-project-type, data-confidential', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'vibe' })
    expect(html).toMatch(/<article data-filterable[^>]*data-tech="/u)
    expect(html).toMatch(/<article data-filterable[^>]*data-project-type="/u)
    expect(html).toMatch(/<article data-filterable[^>]*data-confidential="/u)
  })

  it('Given any render Then skill articles have data-skill-kind', () => {
    const html = renderCvHtml({ locale: 'es', niche: 'generic' })
    expect(html).toContain('data-skill-kind="technical"')
  })

  it('Given enableFilters=true Then experience chips include each seniority', () => {
    const html = renderCvHtml({
      locale: 'es',
      niche: 'generic',
      enableFilters: true,
    })
    expect(html).toContain('data-filter-chip="seniority"')
    expect(html).toMatch(/data-filter-value="senior"/u)
  })

  it('Given enableFilters=true Then chips include project types in HTML', () => {
    const html = renderCvHtml({
      locale: 'es',
      niche: 'vibe',
      enableFilters: true,
    })
    expect(html).toContain('data-filter-chip="projectType"')
  })

  it('Given enableFilters=true Then includes clear-all button', () => {
    const html = renderCvHtml({
      locale: 'es',
      niche: 'generic',
      enableFilters: true,
    })
    expect(html).toContain('data-filter-clear="all"')
  })

  it('Given enableFilters=true Then HTML has data-filter-empty placeholders', () => {
    const html = renderCvHtml({
      locale: 'es',
      niche: 'generic',
      enableFilters: true,
    })
    expect(html).toContain('data-filter-empty')
  })

  it('Given enableFilters=true Then includes hideConfidential chip', () => {
    const html = renderCvHtml({
      locale: 'es',
      niche: 'generic',
      enableFilters: true,
    })
    expect(html).toContain('data-filter-chip="hideConfidential"')
  })
})
