/**
 * @module awards
 * @description 2 premios profesionales. Fuente: .claude/docs/cv/05-premios.md.
 */
import { type Award, AwardSchema } from '../schemas'

const raw: Award[] = [
  {
    slug: 'destacame-innovator-2023',
    title: {
      es: 'Innovador del año 2023 en Destacame',
      en: 'Innovator of the Year 2023 at Destacame',
    },
    issuer: 'Destacame',
    date: '2024-01',
    url: 'https://heyzine.com/flip-book/cdc911b3d1.html',
    motivation: {
      es: 'Por liderar la implementación de soluciones tecnológicas innovadoras en la empresa, mejorando significativamente la eficiencia operativa y la experiencia del usuario.',
      en: 'For leading the implementation of innovative technical solutions across the company, significantly improving operational efficiency and user experience.',
    },
    niches: ['fintech', 'architect', 'leader', 'vibe', 'generic'],
  },
  {
    slug: 'triple-alianza-lima-2020',
    title: {
      es: 'Desafío Triple Alianza Lima — 1er lugar sector Comercio',
      en: 'Triple Alianza Challenge Lima — 1st place, Commerce sector',
    },
    issuer: 'Incubagraria, 1551, StartUpUni',
    date: '2020-11',
    url: 'https://1drv.ms/b/s!AoZaJmtucTrahbFAsRnMKiJDAxBlKg?e=9MKGjP',
    motivation: {
      es: 'Por haber obtenido el 1er lugar en el sector Comercio del Desafío Triple Alianza COVID-19, conseguido durante la experiencia en DIBAL.',
      en: '1st place in the Commerce sector at the Triple Alianza COVID-19 Challenge, achieved during the role at DIBAL.',
    },
    niches: ['leader', 'generic'],
  },
]

export const awards: Award[] = raw.map((a) => AwardSchema.parse(a))
