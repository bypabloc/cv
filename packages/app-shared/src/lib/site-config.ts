/**
 * @module site-config
 * @description Helpers compartidos por TODAS las niche apps + generic.
 *   Cada app pasa su SITE_URL + NICHE y obtiene strings localizadas + meta.
 */
import type { Niche } from '@portfolio/content'

export interface NavItem {
  href: string
  label: string
  /** Si true, abre en otra pestaña / dominio (ej. link al hub desde una app niche). */
  external?: boolean
}

export interface I18nStrings {
  meta: {
    title: string
    description: string
  }
  nav: NavItem[]
  hero: {
    eyebrow: string
    headline: string
    summary: string
    nicheLabel: string
    ctaPrimary: string
    ctaSecondary: string
  }
  stats: {
    eyebrow: string
    yearsExperience: string
    companies: string
    countries: string
    certifications: string
  }
  sections: {
    experience: { title: string; subtitle: string }
    projects: { title: string; subtitle: string }
    skills: { title: string; subtitle: string }
    about: { title: string }
    contact: { title: string; subtitle: string }
    certificates: { title: string; subtitle: string }
    publications: { title: string }
    awards: { title: string; subtitle: string }
    education: { title: string }
    languages: { title: string }
    references: { title: string }
  }
  labels: {
    downloadCv: string
    viewAllExperience: string
    confidential: string
    technicalSkills: string
    softSkills: string
    caseStudyCta: string
    caseStudyProblem: string
    caseStudyProcess: string
    caseStudyResult: string
    caseStudyMetrics: string
  }
  atsKeywords: string[]
}

export interface SiteOverrides {
  metaTitleEs: string
  metaTitleEn: string
  metaDescriptionEs: string
  metaDescriptionEn: string
  heroEyebrowEs?: string
  heroEyebrowEn?: string
  heroHeadlineEs?: string
  heroHeadlineEn?: string
  heroSummaryEs?: string
  heroSummaryEn?: string
  nicheLabelEs?: string
  nicheLabelEn?: string
  experienceSubtitleEs?: string
  experienceSubtitleEn?: string
  projectsSubtitleEs?: string
  projectsSubtitleEn?: string
  atsKeywords?: string[]
  /**
   * Si presente, agrega un item "Otras vistas" / "Other views" al final del
   * nav que apunta al hub multi-niche. Las 5 apps especializadas
   * (fintech, architect, leader, vibe, generic) deben pasar este valor; la
   * app hub debe omitirlo (no se enlaza a si misma).
   */
  hubHref?: string
}

const navEs = (basePrefix: string, hubHref?: string): NavItem[] => {
  const items: NavItem[] = [
    { href: `${basePrefix}/#experience`, label: 'Experiencia' },
    { href: `${basePrefix}/#projects`, label: 'Proyectos' },
    { href: `${basePrefix}/#skills`, label: 'Skills' },
    { href: `${basePrefix}/about`, label: 'Sobre mí' },
    { href: `${basePrefix}/certificates`, label: 'Certificados' },
    { href: `${basePrefix}/contact`, label: 'Contacto' },
  ]
  if (hubHref !== undefined) {
    items.push({ href: hubHref, label: 'Otras vistas' })
  }
  return items
}

const navEn = (basePrefix: string, hubHref?: string): NavItem[] => {
  const items: NavItem[] = [
    { href: `${basePrefix}/#experience`, label: 'Experience' },
    { href: `${basePrefix}/#projects`, label: 'Projects' },
    { href: `${basePrefix}/#skills`, label: 'Skills' },
    { href: `${basePrefix}/about`, label: 'About' },
    { href: `${basePrefix}/certificates`, label: 'Certificates' },
    { href: `${basePrefix}/contact`, label: 'Contact' },
  ]
  if (hubHref !== undefined) {
    items.push({ href: hubHref, label: 'Other views' })
  }
  return items
}

export function buildStrings(
  overrides: SiteOverrides,
): Record<'es' | 'en', I18nStrings> {
  return {
    es: {
      meta: {
        title: overrides.metaTitleEs,
        description: overrides.metaDescriptionEs,
      },
      nav: navEs('', overrides.hubHref),
      hero: {
        eyebrow:
          overrides.heroEyebrowEs ??
          'Pablo Contreras · Lima, Perú · Disponible remoto LATAM/US',
        headline: overrides.heroHeadlineEs ?? 'Senior Full Stack Engineer',
        summary:
          overrides.heroSummaryEs ??
          'Más de 12 años entregando producto. Especialización en fintech LATAM, microservicios, AWS y plataformas Vue / Django.',
        nicheLabel: overrides.nicheLabelEs ?? 'Full Stack',
        ctaPrimary: 'Ver experiencia',
        ctaSecondary: 'Descargar CV',
      },
      stats: {
        eyebrow: 'Track record',
        yearsExperience: 'Años entregando producto',
        companies: 'Empresas',
        countries: 'Países LATAM',
        certifications: 'Certificaciones',
      },
      sections: {
        experience: {
          title: 'Experiencia',
          subtitle:
            overrides.experienceSubtitleEs ??
            '9 puestos en 8 empleadores. Especialización en fintech LATAM y plataformas full stack.',
        },
        projects: {
          title: 'Proyectos destacados',
          subtitle:
            overrides.projectsSubtitleEs ??
            'Side projects abiertos y case studies bajo NDA con métricas reales.',
        },
        skills: {
          title: 'Skills técnicas',
          subtitle:
            'Stack actual + dominios donde he entregado producto en producción.',
        },
        about: { title: 'Sobre mí' },
        contact: {
          title: 'Contacto',
          subtitle:
            'Mejor por email o LinkedIn. Suelo responder en menos de 24 h.',
        },
        certificates: {
          title: 'Certificados',
          subtitle: 'Certificaciones técnicas relevantes para este perfil.',
        },
        publications: { title: 'Publicaciones' },
        awards: {
          title: 'Premios',
          subtitle: 'Reconocimientos por impacto técnico y de negocio.',
        },
        education: { title: 'Educación' },
        languages: { title: 'Idiomas' },
        references: { title: 'Referencias' },
      },
      labels: {
        downloadCv: 'Descargar CV',
        viewAllExperience: 'Ver toda la experiencia',
        confidential: 'Bajo NDA — métricas detalladas en privado',
        technicalSkills: 'Técnicas',
        softSkills: 'Blandas',
        caseStudyCta: 'Ver caso de estudio',
        caseStudyProblem: 'Problema',
        caseStudyProcess: 'Proceso',
        caseStudyResult: 'Resultado',
        caseStudyMetrics: 'Métricas',
      },
      atsKeywords: overrides.atsKeywords ?? [],
    },
    en: {
      meta: {
        title: overrides.metaTitleEn,
        description: overrides.metaDescriptionEn,
      },
      nav: navEn('/en', overrides.hubHref),
      hero: {
        eyebrow:
          overrides.heroEyebrowEn ??
          'Pablo Contreras · Lima, Peru · Remote-friendly LATAM/US',
        headline: overrides.heroHeadlineEn ?? 'Senior Full Stack Engineer',
        summary:
          overrides.heroSummaryEn ??
          '12+ years shipping product. Specialized in LATAM fintech, microservices, AWS and Vue / Django platforms.',
        nicheLabel: overrides.nicheLabelEn ?? 'Full Stack',
        ctaPrimary: 'View experience',
        ctaSecondary: 'Download CV',
      },
      stats: {
        eyebrow: 'Track record',
        yearsExperience: 'Years shipping product',
        companies: 'Companies',
        countries: 'LATAM countries',
        certifications: 'Certifications',
      },
      sections: {
        experience: {
          title: 'Experience',
          subtitle:
            overrides.experienceSubtitleEn ??
            '9 roles in 8 employers. Focus on LATAM fintech and full stack platforms.',
        },
        projects: {
          title: 'Featured projects',
          subtitle:
            overrides.projectsSubtitleEn ??
            'Open side projects and case studies under NDA with real metrics.',
        },
        skills: {
          title: 'Technical skills',
          subtitle:
            'Current stack + domains where I have shipped to production.',
        },
        about: { title: 'About' },
        contact: {
          title: 'Contact',
          subtitle: 'Email or LinkedIn work best. Typical response under 24h.',
        },
        certificates: {
          title: 'Certificates',
          subtitle: 'Technical certifications relevant for this profile.',
        },
        publications: { title: 'Publications' },
        awards: {
          title: 'Awards',
          subtitle: 'Recognition for technical and business impact.',
        },
        education: { title: 'Education' },
        languages: { title: 'Languages' },
        references: { title: 'References' },
      },
      labels: {
        downloadCv: 'Download CV',
        viewAllExperience: 'View full experience',
        confidential: 'Under NDA — detailed metrics on request',
        technicalSkills: 'Technical',
        softSkills: 'Soft',
        caseStudyCta: 'View case study',
        caseStudyProblem: 'Problem',
        caseStudyProcess: 'Process',
        caseStudyResult: 'Result',
        caseStudyMetrics: 'Metrics',
      },
      atsKeywords: overrides.atsKeywords ?? [],
    },
  }
}

export interface SiteContext {
  niche: Niche
  siteUrl: string
  strings: Record<'es' | 'en', I18nStrings>
}
