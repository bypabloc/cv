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
  type Niche,
} from '@portfolio/content'

/** Item de navegacion ya resuelto (con href listo para render). */
export interface NavItem {
  href: string
  label: string
  /** Si true, abre en otra pestaña / dominio (ej. link al hub). */
  external?: boolean
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
    confidential: string
    technicalSkills: string
    softSkills: string
    caseStudyCta: string
    caseStudyProblem: string
    caseStudyProcess: string
    caseStudyResult: string
    caseStudyMetrics: string
  }
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
 * Construye los items de nav resueltos. El item `hub` solo se incluye si la
 * app pasa `hubHref` (las 5 apps niche lo pasan; la app hub lo omite).
 */
function buildNav(
  elements: ElementsStrings,
  locale: 'es' | 'en',
  hubHref?: string,
): NavItem[] {
  const basePrefix = locale === 'es' ? '' : '/en'
  const items: NavItem[] = []
  for (const item of elements.nav) {
    if (item.key === 'hub') {
      if (hubHref === undefined) continue
      items.push({
        href: hubHref,
        label: item.label,
        external: true,
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
 *   (textos del CV). El `hubHref` agrega el item "Otras vistas" al nav.
 *
 * @param app - App del monorepo (generic | hub | fintech | architect | leader | vibe)
 * @param hubHref - URL del hub. Si se pasa, el nav incluye el item al hub.
 *
 * @returns Record es/en con las strings completas de la app.
 *
 * @example
 *   const STRINGS = buildStrings('fintech', SITE_URLS.hub)
 *   STRINGS.es.hero.headline   // del curriculum/fintech.es.yaml
 *   STRINGS.es.sections.experience.title  // del elements.es.yaml
 */
export function buildStrings(
  app: CurriculumApp,
  hubHref?: string,
): Record<'es' | 'en', I18nStrings> {
  const compose = (locale: 'es' | 'en'): I18nStrings => {
    const el = getElements(locale)
    const cv = getCurriculum(app, locale)
    return {
      meta: { ...cv.meta },
      nav: buildNav(el, locale, hubHref),
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
        confidential: el.labels.confidential,
        technicalSkills: el.labels.technicalSkills,
        softSkills: el.labels.softSkills,
        caseStudyCta: el.labels.caseStudyCta,
        caseStudyProblem: el.labels.caseStudyProblem,
        caseStudyProcess: el.labels.caseStudyProcess,
        caseStudyResult: el.labels.caseStudyResult,
        caseStudyMetrics: el.labels.caseStudyMetrics,
      },
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
