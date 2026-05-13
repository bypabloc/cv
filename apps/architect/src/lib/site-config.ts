/**
 * @module site-config (architect)
 * @description Config especifica del sitio architect. Delega a `defineSiteConfig`
 *   del paquete compartido — solo declara los overrides unicos del sitio.
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'architect',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
  overrides: {
    metaTitleEs: 'Pablo Contreras — Frontend Architect & Microservicios',
    metaTitleEn: 'Pablo Contreras — Frontend Architect & Microservices',
    metaDescriptionEs:
      'Arquitecto Frontend con experiencia en microservicios, microfrontends y sistemas escalables. Vue/Nuxt + Django + AWS. Decisiones de diseño y arquitectura documentadas.',
    metaDescriptionEn:
      'Frontend Architect experienced in microservices, microfrontends and scalable systems. Vue/Nuxt + Django + AWS. Documented design and architecture decisions.',
    heroEyebrowEs: 'Pablo Contreras · Architect · Lima, Perú',
    heroEyebrowEn: 'Pablo Contreras · Architect · Lima, Peru',
    heroHeadlineEs: 'Frontend Architect & Microservicios',
    heroHeadlineEn: 'Frontend Architect & Microservices',
    heroSummaryEs:
      'Diseño y entrego sistemas distribuidos: microfrontend Vue/Nuxt + 8+ microservicios Django sobre AWS. Cada decisión arquitectónica está documentada y testeada en producción fintech.',
    heroSummaryEn:
      'I design and ship distributed systems: Vue/Nuxt microfrontend + 8+ Django microservices on AWS. Every architectural decision is documented and tested in fintech production.',
    nicheLabelEs: 'Architect',
    nicheLabelEn: 'Architect',
    experienceSubtitleEs:
      'Roles de arquitectura y liderazgo técnico destacados (Destacame, Dibal).',
    experienceSubtitleEn:
      'Architecture and tech leadership roles first (Destacame, Dibal).',
    projectsSubtitleEs:
      'Proyectos con decisiones arquitectónicas explícitas y stack documentado.',
    projectsSubtitleEn:
      'Projects with explicit architectural decisions and a documented stack.',
    atsKeywords: [
      'Frontend Architect',
      'Software Architect',
      'Microservices',
      'Microfrontend',
      'Distributed Systems',
      'System Design',
      'Vue 3',
      'Nuxt',
      'TypeScript',
      'Django',
      'AWS',
      'EC2',
      'RDS',
      'S3',
      'AutoScaling',
      'API Gateway',
      'PostgreSQL',
      'Clean Architecture',
    ],
  },
})
