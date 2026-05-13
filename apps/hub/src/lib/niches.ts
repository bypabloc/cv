/**
 * @module niches
 * @description Definicion de las 5 cards del hub selector.
 */
import type { Niche } from '@portfolio/content'

export interface NicheCard {
  niche: Niche
  url: string
  title: { es: string; en: string }
  blurb: { es: string; en: string }
  accent: string
}

export const NICHE_CARDS: NicheCard[] = [
  {
    niche: 'generic',
    url: 'https://hub.the-full-stack.com',
    title: { es: 'Full Stack Senior', en: 'Senior Full Stack' },
    blurb: {
      es: 'Vue + Django + AWS · 8 años · todas las skills',
      en: 'Vue + Django + AWS · 8 years · all skills',
    },
    accent: '#9e9e99',
  },
  {
    niche: 'fintech',
    url: 'https://fintech.the-full-stack.com',
    title: { es: 'Fintech LATAM', en: 'LATAM Fintech' },
    blurb: {
      es: 'Chile, México · saldar deudas · scoring · créditos',
      en: 'Chile, Mexico · debt settlement · scoring · credit',
    },
    accent: '#4f6ef7',
  },
  {
    niche: 'architect',
    url: 'https://architect.the-full-stack.com',
    title: { es: 'Architect', en: 'Architect' },
    blurb: {
      es: 'Microservicios · microfrontend · sistemas escalables',
      en: 'Microservices · microfrontend · scalable systems',
    },
    accent: '#38d9d6',
  },
  {
    niche: 'leader',
    url: 'https://leader.the-full-stack.com',
    title: { es: 'Tech Lead', en: 'Tech Lead' },
    blurb: {
      es: 'Liderazgo de equipos · mentoring · entregar producto',
      en: 'Team leadership · mentoring · shipping product',
    },
    accent: '#f4b740',
  },
  {
    niche: 'vibe',
    url: 'https://vibe.the-full-stack.com',
    title: { es: 'Vibe Coding', en: 'Vibe Coding' },
    blurb: {
      es: 'Claude Code · Cursor · dev tools · workflows IA',
      en: 'Claude Code · Cursor · dev tools · AI workflows',
    },
    accent: '#f06e9c',
  },
]
