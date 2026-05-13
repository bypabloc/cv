/**
 * @module site-config
 * @description Helpers compartidos por TODAS las niche apps + generic.
 *   Cada app pasa su SITE_URL + NICHE y obtiene strings localizadas + meta.
 */
import type { Niche } from '@portfolio/content'

export interface NavItem {
  href: string
  label: string
}

export interface I18nStrings {
  meta: {
    title: string
    description: string
  }
  nav: NavItem[]
  hero: {
    eyebrow: string
    ctaPrimary: string
    ctaSecondary: string
  }
  sections: {
    experience: { title: string; subtitle: string }
    projects: { title: string; subtitle: string }
    skills: { title: string; subtitle: string }
    about: { title: string }
    contact: { title: string; subtitle: string }
    certificates: { title: string; subtitle: string }
    publications: { title: string }
    awards: { title: string }
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
  }
}

interface SiteOverrides {
  metaTitleEs: string
  metaTitleEn: string
  metaDescriptionEs: string
  metaDescriptionEn: string
  heroEyebrowEs?: string
  heroEyebrowEn?: string
  experienceSubtitleEs?: string
  experienceSubtitleEn?: string
  projectsSubtitleEs?: string
  projectsSubtitleEn?: string
}

const navEs = (basePrefix: string): NavItem[] => [
  { href: `${basePrefix}/#experience`, label: 'Experiencia' },
  { href: `${basePrefix}/#projects`, label: 'Proyectos' },
  { href: `${basePrefix}/#skills`, label: 'Skills' },
  { href: `${basePrefix}/about`, label: 'Sobre mí' },
  { href: `${basePrefix}/certificates`, label: 'Certificados' },
  { href: `${basePrefix}/#contact`, label: 'Contacto' },
]

const navEn = (basePrefix: string): NavItem[] => [
  { href: `${basePrefix}/#experience`, label: 'Experience' },
  { href: `${basePrefix}/#projects`, label: 'Projects' },
  { href: `${basePrefix}/#skills`, label: 'Skills' },
  { href: `${basePrefix}/about`, label: 'About' },
  { href: `${basePrefix}/certificates`, label: 'Certificates' },
  { href: `${basePrefix}/#contact`, label: 'Contact' },
]

export function buildStrings(
  overrides: SiteOverrides,
): Record<'es' | 'en', I18nStrings> {
  return {
    es: {
      meta: {
        title: overrides.metaTitleEs,
        description: overrides.metaDescriptionEs,
      },
      nav: navEs(''),
      hero: {
        eyebrow: overrides.heroEyebrowEs ?? 'Pablo Contreras · Lima, Perú',
        ctaPrimary: 'Ver experiencia',
        ctaSecondary: 'Descargar CV',
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
        awards: { title: 'Premios' },
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
      },
    },
    en: {
      meta: {
        title: overrides.metaTitleEn,
        description: overrides.metaDescriptionEn,
      },
      nav: navEn('/en'),
      hero: {
        eyebrow: overrides.heroEyebrowEn ?? 'Pablo Contreras · Lima, Peru',
        ctaPrimary: 'View experience',
        ctaSecondary: 'Download CV',
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
        awards: { title: 'Awards' },
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
      },
    },
  }
}

export interface SiteContext {
  niche: Niche
  siteUrl: string
  strings: Record<'es' | 'en', I18nStrings>
}
