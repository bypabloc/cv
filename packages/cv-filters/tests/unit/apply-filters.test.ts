/**
 * @description Tests para applyFilters() sobre un DOM construido via happy-dom.
 *   Cubre AC-9 (default sin filtros), AC-14 (recalculo stats), AC-15 (empty
 *   state).
 */
import { beforeEach, describe, expect, it } from 'vitest'
import { applyFilters } from '../../src/apply-filters'
import { emptyFilterState } from '../../src/types'

function buildDom() {
  document.body.innerHTML = `
    <div data-stats-host>
      <span data-stat="years">0</span>
      <span data-stat="companies">0</span>
      <span data-stat="certifications">0</span>
    </div>

    <section data-filter-section="experience">
      <article
        data-filterable
        data-tech="Vue,TypeScript"
        data-seniority="senior"
        data-start="2022-01"
        data-end="2024-12"
        data-company="Acme"
      >Exp Acme</article>
      <article
        data-filterable
        data-tech="Python,Django"
        data-seniority="lead"
        data-start="2020-01"
        data-end="2021-12"
        data-company="Beta"
      >Exp Beta</article>
      <p data-filter-empty hidden>No experiences</p>
    </section>

    <section data-filter-section="project">
      <article
        data-filterable
        data-tech="Vue"
        data-project-type="web"
        data-confidential="false"
      >Proj A</article>
      <article
        data-filterable
        data-tech="Python"
        data-project-type="ai"
        data-confidential="true"
      >Proj B</article>
      <p data-filter-empty hidden>No projects</p>
    </section>

    <section data-filter-section="certificate">
      <article data-filterable data-tech="AWS">Cert 1</article>
      <article data-filterable data-tech="Vue">Cert 2</article>
    </section>
  `
}

describe('applyFilters [AC-9 default]', () => {
  beforeEach(() => buildDom())

  it('Given empty state Then all items remain visible', () => {
    const result = applyFilters(emptyFilterState())
    expect(result.totalAll).toBe(6)
    expect(result.totalVisible).toBe(6)
  })

  it('Given empty state Then no items have hidden attr', () => {
    applyFilters(emptyFilterState())
    const items = document.querySelectorAll('[data-filterable]')
    for (const item of items) {
      expect(item.hasAttribute('hidden')).toBe(false)
    }
  })
})

describe('applyFilters [AC-4 tech filter]', () => {
  beforeEach(() => buildDom())

  it('Given tech=[Vue] Then only items with Vue remain visible', () => {
    const result = applyFilters({ ...emptyFilterState(), tech: ['Vue'] })
    expect(result.totalVisible).toBe(3) // Exp Acme + Proj A + Cert 2
  })

  it('Given tech=[Python] Then Python items remain visible', () => {
    const result = applyFilters({ ...emptyFilterState(), tech: ['Python'] })
    expect(result.totalVisible).toBe(2) // Exp Beta + Proj B
  })
})

describe('applyFilters [AC-8 hideConfidential]', () => {
  beforeEach(() => buildDom())

  it('Given hideConfidential=true Then confidential items are hidden', () => {
    applyFilters({ ...emptyFilterState(), hideConfidential: true })
    const confidentialItem = document.querySelector(
      '[data-confidential="true"]',
    )
    expect(confidentialItem?.hasAttribute('hidden')).toBe(true)
  })

  it('Given hideConfidential=false Then all items remain visible', () => {
    applyFilters({ ...emptyFilterState(), hideConfidential: false })
    const confidentialItem = document.querySelector(
      '[data-confidential="true"]',
    )
    expect(confidentialItem?.hasAttribute('hidden')).toBe(false)
  })
})

describe('applyFilters [AC-15 empty state messages]', () => {
  beforeEach(() => buildDom())

  it('Given filter that hides all experiences Then empty state shows', () => {
    applyFilters({ ...emptyFilterState(), tech: ['Rust'] })
    const expEmpty = document
      .querySelector('[data-filter-section="experience"]')
      ?.querySelector('[data-filter-empty]')
    expect(expEmpty?.hasAttribute('hidden')).toBe(false)
  })

  it('Given some experiences visible Then empty state hidden', () => {
    applyFilters({ ...emptyFilterState(), tech: ['Vue'] })
    const expEmpty = document
      .querySelector('[data-filter-section="experience"]')
      ?.querySelector('[data-filter-empty]')
    expect(expEmpty?.hasAttribute('hidden')).toBe(true)
  })

  it('Given empty state Then sections with no items show empty (defensive)', () => {
    document.body.innerHTML = `
      <section data-filter-section="experience">
        <p data-filter-empty hidden>nothing</p>
      </section>
    `
    const result = applyFilters(emptyFilterState())
    expect(result.visibleBySection.experience).toBeUndefined()
  })
})

describe('applyFilters [AC-14 stats recalculation]', () => {
  beforeEach(() => buildDom())

  it('Given empty state Then stats reflect all experiences', () => {
    applyFilters(emptyFilterState())
    const years = document.querySelector('[data-stat="years"]')?.textContent
    const companies = document.querySelector(
      '[data-stat="companies"]',
    )?.textContent
    // earliest 2020-01, now varies -> assert que es un numero coherente
    expect(Number(years)).toBeGreaterThanOrEqual(3)
    expect(companies).toBe('2')
  })

  it('Given filter that hides 1 experience Then stats reflect 1 visible', () => {
    applyFilters({ ...emptyFilterState(), tech: ['Vue'] })
    const companies = document.querySelector(
      '[data-stat="companies"]',
    )?.textContent
    expect(companies).toBe('1') // solo Acme queda
  })

  it('Given filter that hides all experiences Then years and companies are 0', () => {
    applyFilters({ ...emptyFilterState(), tech: ['Rust'] })
    const years = document.querySelector('[data-stat="years"]')?.textContent
    const companies = document.querySelector(
      '[data-stat="companies"]',
    )?.textContent
    expect(years).toBe('0')
    expect(companies).toBe('0')
  })

  it('Given certificates filtered Then certifications count updates', () => {
    applyFilters({ ...emptyFilterState(), tech: ['Vue'] })
    const certs = document.querySelector(
      '[data-stat="certifications"]',
    )?.textContent
    expect(certs).toBe('1') // solo Cert 2 (Vue) queda
  })
})

describe('applyFilters result structure', () => {
  beforeEach(() => buildDom())

  it('Given filter Then result includes section breakdown', () => {
    const result = applyFilters({ ...emptyFilterState(), tech: ['Vue'] })
    expect(result.visibleBySection.experience).toBe(1)
    expect(result.visibleBySection.project).toBe(1)
    expect(result.visibleBySection.certificate).toBe(1)
  })

  it('Given no items in DOM Then totals are 0', () => {
    document.body.innerHTML = ''
    const result = applyFilters(emptyFilterState())
    expect(result.totalAll).toBe(0)
    expect(result.totalVisible).toBe(0)
  })
})
