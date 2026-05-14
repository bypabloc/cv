/**
 * @module site-config (fintech)
 * @description Config especifica del sitio fintech. Delega a `defineSiteConfig`
 *   del paquete compartido — solo declara los overrides unicos del sitio.
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'fintech',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
  overrides: {
    metaTitleEs: 'Pablo Contreras — Senior Full Stack Fintech LATAM',
    metaTitleEn: 'Pablo Contreras — Senior Full Stack LATAM Fintech',
    metaDescriptionEs:
      'Senior Full Stack especializado en fintech Chile/México. Saldar deudas, scoring crediticio, productos de crédito con Vue + Django + AWS. 8+ años entregando producto.',
    metaDescriptionEn:
      'Senior Full Stack specialized in LATAM fintech (Chile, Mexico). Debt settlement, credit scoring and credit products with Vue + Django + AWS. 8+ years shipping product.',
    heroEyebrowEs:
      'Pablo Contreras · Fintech LATAM · Lima, Perú · Remoto LATAM/US',
    heroEyebrowEn:
      'Pablo Contreras · LATAM Fintech · Lima, Peru · Remote LATAM/US',
    heroHeadlineEs: 'Senior Full Stack Fintech LATAM',
    heroHeadlineEn: 'Senior Full Stack LATAM Fintech',
    heroSummaryEs:
      'Entrego productos fintech en Chile y México desde Destacame: saldar deudas, scoring crediticio y créditos por tramos. Vue + Nuxt + Django + AWS + microservicios con foco en compliance y experiencia del usuario.',
    heroSummaryEn:
      'I ship fintech products in Chile and Mexico from Destacame: debt settlement, credit scoring and tiered credit. Vue + Nuxt + Django + AWS + microservices with focus on compliance and user experience.',
    nicheLabelEs: 'Fintech LATAM',
    nicheLabelEn: 'LATAM Fintech',
    experienceSubtitleEs:
      'Roles fintech destacados primero: Destacame (Chile, México) y GoodMeal.',
    experienceSubtitleEn:
      'Fintech roles first: Destacame (Chile, Mexico) and GoodMeal.',
    projectsSubtitleEs:
      'Case studies de productos fintech LATAM (bajo NDA) + side projects.',
    projectsSubtitleEn:
      'Case studies of LATAM fintech products (under NDA) + side projects.',
    atsKeywords: [
      'Senior Full Stack Developer',
      'Fintech LATAM',
      'Chile',
      'México',
      'Debt Settlement',
      'Credit Scoring',
      'Tiered Credit Products',
      'Microservicios',
      'Vue 3',
      'Nuxt',
      'Django',
      'Python',
      'TypeScript',
      'AWS',
      'PostgreSQL',
      'PCI DSS awareness',
      'KYC / AML',
      'PII handling',
    ],
  },
})
