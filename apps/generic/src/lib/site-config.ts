/**
 * @module site-config (generic)
 * @description Config especifica del sitio generic. Delega a `defineSiteConfig`
 *   del paquete compartido — solo declara los overrides unicos del sitio.
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'generic',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
  overrides: {
    metaTitleEs: 'Pablo Contreras — Ingeniero Full Stack senior',
    metaTitleEn: 'Pablo Contreras — Senior Full Stack Engineer',
    metaDescriptionEs:
      'Ingeniero Full Stack con 12+ años en Vue, Nuxt, Django, AWS y fintech LATAM (Chile, México). Portfolio + experiencia + proyectos.',
    metaDescriptionEn:
      'Senior Full Stack Engineer with 12+ years in Vue, Nuxt, Django, AWS and LATAM fintech (Chile, Mexico). Portfolio + experience + projects.',
    heroHeadlineEs: 'Senior Full Stack Engineer',
    heroHeadlineEn: 'Senior Full Stack Engineer',
    heroSummaryEs:
      'Más de 12 años entregando producto fintech LATAM, sistemas ERP y e-commerce. Stack actual: Vue 3 + Nuxt + Django + AWS + microservicios. Especialización transversal: fintech, arquitectura, tech leadership y vibe coding con Claude Code.',
    heroSummaryEn:
      '12+ years shipping LATAM fintech products, ERP systems and e-commerce. Current stack: Vue 3 + Nuxt + Django + AWS + microservices. Cross-cutting expertise: fintech, architecture, tech leadership and vibe coding with Claude Code.',
    nicheLabelEs: 'Full Stack',
    nicheLabelEn: 'Full Stack',
    atsKeywords: [
      'Senior Full Stack Developer',
      'Senior Software Engineer',
      'Vue 3',
      'Nuxt',
      'TypeScript',
      'Django',
      'Python',
      'AWS',
      'Microservicios',
      'PostgreSQL',
      'Fintech LATAM',
      'Tech Lead',
      'Architect',
      'Claude Code',
    ],
  },
})
