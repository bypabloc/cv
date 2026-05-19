/**
 * @description Tests para buildStrings. Cubre AC-4 (una app usa su propio
 *   curriculum + los labels comunes de elements) y AC-5 (claves de seccion
 *   sin override caen al _base).
 */
import { describe, expect, it } from 'vitest'
import { buildStrings } from '../../../src/lib/site-config'

describe('buildStrings', () => {
  it('Given app vibe When built Then hero comes from the vibe curriculum', () => {
    const strings = buildStrings('vibe')
    expect(strings.es.hero.headline).toBe(
      'AI-Augmented Full Stack · Claude Code',
    )
    expect(strings.es.hero.nicheLabel).toBe('Vibe Coding')
  })

  it('Given app vibe When built Then section titles come from the shared elements', () => {
    const strings = buildStrings('vibe')
    expect(strings.es.sections.experience.title).toBe('Experiencia')
    expect(strings.en.sections.experience.title).toBe('Experience')
  })

  it('Given app vibe When built Then experience subtitle comes from the vibe curriculum', () => {
    const strings = buildStrings('vibe')
    expect(strings.es.sections.experience.subtitle).toBe(
      'Roles donde integro IA en el día a día (Destacame actual).',
    )
  })

  it('Given app vibe When built Then certificates subtitle falls back to _base (no override)', () => {
    const strings = buildStrings('vibe')
    expect(strings.es.sections.certificates.subtitle).toBe(
      'Certificaciones técnicas relevantes para este perfil.',
    )
  })

  it('Given a hubHref When built Then the nav includes the hub item with that href', () => {
    const strings = buildStrings('fintech', 'https://hub.example.test')
    const hubItem = strings.es.nav.find((n) => n.label === 'Otras vistas')
    expect(hubItem).toEqual({
      href: 'https://hub.example.test',
      label: 'Otras vistas',
      external: true,
    })
  })

  it('Given no hubHref When built Then the nav has no hub item', () => {
    const strings = buildStrings('fintech')
    const hubItem = strings.es.nav.find((n) => n.label === 'Otras vistas')
    expect(hubItem).toBe(undefined)
  })

  it('Given the en locale When built Then nav hrefs are prefixed with /en', () => {
    const strings = buildStrings('generic')
    const about = strings.en.nav.find((n) => n.label === 'About')
    expect(about?.href).toBe('/en/about')
  })

  it('Given any app When built Then component strings are present', () => {
    const strings = buildStrings('architect')
    expect(strings.es.components.contactForm.submit).toBe('Enviar')
    expect(strings.es.components.footer.manageConsent).toBe(
      'Gestionar consentimiento',
    )
  })
})
