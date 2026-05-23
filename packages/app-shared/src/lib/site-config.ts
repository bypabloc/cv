/**
 * @module site-config
 * @description Compone las strings localizadas de un sitio del portfolio a
 *   partir de los YAML i18n de `@portfolio/content`:
 *
 *   - `elements`   -> labels reutilizables (nav, stats, secciones, labels)
 *   - `curriculum` -> textos del CV especificos de la app (meta, hero)
 *
 *   `buildStrings(app, locale)` los funde en el objeto `I18nStrings` que
 *   consumen `PageLayout`, `CvSections` y los componentes. Los textos NO
 *   viven aqui: viven en `packages/content/src/data/i18n/*.yaml`.
 */
import {
  type CurriculumApp,
  type ElementsStrings,
  getCurriculum,
  getElements,
  NICHES,
  type Niche,
} from '@portfolio/content'
import { SITE_URLS } from './site-urls'

/** Sub-item de un nav dropdown. */
export interface NavDropdownItem {
  href: string
  label: string
  /** Niche al que apunta (usado para CSS hooks). */
  niche?: string
  /** True si esta entry corresponde al niche/sitio actual. */
  current?: boolean
}

/** Item de navegacion ya resuelto (con href listo para render). */
export interface NavItem {
  href: string
  label: string
  /** Si true, abre en otra pestaña / dominio (ej. link al hub). */
  external?: boolean
  /** Si esta presente, el item es un dropdown con las sub-entries listadas. */
  dropdownItems?: NavDropdownItem[]
}

/**
 * Strings localizadas que consume un sitio. La forma se mantiene estable
 * para no romper los componentes; las fuentes son los YAML i18n.
 */
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
  stats: ElementsStrings['stats']
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
    home: string
    downloadCv: string
    viewAllExperience: string
    viewDetail: string
    viewSite: string
    viewRepo: string
    currentView: string
    confidential: string
    technicalSkills: string
    softSkills: string
    responsibilities: string
    achievements: string
    caseStudyCta: string
    caseStudyProblem: string
    caseStudyProcess: string
    caseStudyResult: string
    caseStudyMetrics: string
    ctaPrimary: string
    ctaSecondary: string
  }
  /** Etiquetas de los 5 niches (usado por el dropdown del nav). */
  nicheLabels: ElementsStrings['nicheLabels']
  /** Strings de los componentes interactivos (form, footer, nav, ...). */
  components: ElementsStrings['components']
  /** Meta de las paginas secundarias (about, certificates, contact). */
  pages: ElementsStrings['pages']
  atsKeywords: string[]
}

/** Path absoluto/relativo de cada item de nav segun su `key` + prefijo. */
function navHrefFor(key: string, basePrefix: string, hubHref?: string): string {
  switch (key) {
    case 'experience':
      return `${basePrefix}/#experience`
    case 'projects':
      return `${basePrefix}/#projects`
    case 'skills':
      return `${basePrefix}/#skills`
    case 'about':
      return `${basePrefix}/about`
    case 'certificates':
      return `${basePrefix}/certificates`
    case 'contact':
      return `${basePrefix}/contact`
    case 'hub':
      return hubHref ?? ''
    default:
      return `${basePrefix}/`
  }
}

/**
 * Construye los items de nav resueltos. El item `hub` se reemplaza por un
 * dropdown con los 5 niches del portfolio (cross-subdomain, navegacion en
 * la misma pestana). Se incluye solo si la app pasa `currentNiche` (las
 * 5 apps niche lo pasan; la app hub lo omite).
 */
function buildNav(
  elements: ElementsStrings,
  locale: 'es' | 'en',
  currentNiche: Niche | null,
): NavItem[] {
  const basePrefix = locale === 'es' ? '' : '/en'
  const items: NavItem[] = []
  for (const item of elements.nav) {
    if (item.key === 'hub') {
      if (currentNiche === null) continue
      items.push({
        href: '',
        label: item.label,
        dropdownItems: NICHES.map((n) => ({
          href: SITE_URLS[n],
          label: elements.nicheLabels[n],
          niche: n,
          current: n === currentNiche,
        })),
      })
      continue
    }
    items.push({ href: navHrefFor(item.key, basePrefix), label: item.label })
  }
  return items
}

/**
 * @function buildStrings
 * @description Compone el `I18nStrings` de una app en ambos idiomas, fundiendo
 *   los `elements` (labels reutilizables) con el `curriculum` de la app
 *   (textos del CV). El `currentNiche` agrega el item dropdown "Otras vistas"
 *   con los 5 niches; pasar `null` (caso app hub) lo omite.
 *
 * @param app - App del monorepo (generic | hub | fintech | architect | leader | vibe)
 * @param currentNiche - Niche del sitio actual. Si `null`, omite el dropdown del nav.
 *
 * @returns Record es/en con las strings completas de la app.
 *
 * @example
 *   const STRINGS = buildStrings('fintech', 'fintech')
 *   STRINGS.es.hero.headline   // del curriculum/fintech.es.yaml
 *   STRINGS.es.sections.experience.title  // del elements.es.yaml
 */
export function buildStrings(
  app: CurriculumApp,
  currentNiche: Niche | null,
): Record<'es' | 'en', I18nStrings> {
  const compose = (locale: 'es' | 'en'): I18nStrings => {
    const el = getElements(locale)
    const cv = getCurriculum(app, locale)
    return {
      meta: { ...cv.meta },
      nav: buildNav(el, locale, currentNiche),
      hero: {
        eyebrow: cv.hero.eyebrow,
        headline: cv.hero.headline,
        summary: cv.hero.summary,
        nicheLabel: cv.hero.nicheLabel,
        ctaPrimary: el.labels.ctaPrimary,
        ctaSecondary: el.labels.ctaSecondary,
      },
      stats: el.stats,
      sections: {
        experience: {
          title: el.sections.experience.title,
          subtitle: cv.sections.experienceSubtitle,
        },
        projects: {
          title: el.sections.projects.title,
          subtitle: cv.sections.projectsSubtitle,
        },
        skills: {
          title: el.sections.skills.title,
          subtitle: cv.sections.skillsSubtitle,
        },
        about: { title: el.sections.about.title },
        contact: {
          title: el.sections.contact.title,
          subtitle: cv.sections.contactSubtitle,
        },
        certificates: {
          title: el.sections.certificates.title,
          subtitle: cv.sections.certificatesSubtitle,
        },
        publications: { title: el.sections.publications.title },
        awards: {
          title: el.sections.awards.title,
          subtitle: cv.sections.awardsSubtitle,
        },
        education: { title: el.sections.education.title },
        languages: { title: el.sections.languages.title },
        references: { title: el.sections.references.title },
      },
      labels: {
        home: el.labels.home,
        downloadCv: el.labels.downloadCv,
        viewAllExperience: el.labels.viewAllExperience,
        viewDetail: el.labels.viewDetail,
        viewSite: el.labels.viewSite,
        viewRepo: el.labels.viewRepo,
        currentView: el.labels.currentView,
        confidential: el.labels.confidential,
        technicalSkills: el.labels.technicalSkills,
        softSkills: el.labels.softSkills,
        responsibilities: el.labels.responsibilities,
        achievements: el.labels.achievements,
        caseStudyCta: el.labels.caseStudyCta,
        caseStudyProblem: el.labels.caseStudyProblem,
        caseStudyProcess: el.labels.caseStudyProcess,
        caseStudyResult: el.labels.caseStudyResult,
        caseStudyMetrics: el.labels.caseStudyMetrics,
        ctaPrimary: el.labels.ctaPrimary,
        ctaSecondary: el.labels.ctaSecondary,
      },
      nicheLabels: el.nicheLabels,
      components: el.components,
      pages: el.pages,
      atsKeywords: [...cv.atsKeywords],
    }
  }
  return { es: compose('es'), en: compose('en') }
}

export interface SiteContext {
  niche: Niche
  siteUrl: string
  strings: Record<'es' | 'en', I18nStrings>
}
