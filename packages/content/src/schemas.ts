/**
 * @schema portfolio-schemas
 * @description Zod schemas de toda la data del CV. Fuente de verdad de tipos.
 *   Cada entry (experience, project, certificate, etc.) tiene niches[] para
 *   permitir filtrado por nicho en cada app.
 *
 * @example
 *   import { ExperienceSchema, type Experience } from '@portfolio/content'
 *   const e: Experience = ExperienceSchema.parse(rawData)
 */
import { z } from 'zod'

/** Niches soportados — UNA fuente de verdad para todo el monorepo. */
export const NICHES = [
  'fintech',
  'architect',
  'leader',
  'vibe',
  'generic',
] as const

export const NicheSchema = z.enum(NICHES)
export type Niche = z.infer<typeof NicheSchema>

/** YYYY-MM (ej. "2024-01"). Validado por regex. */
export const YearMonthSchema = z
  .string()
  .regex(/^\d{4}-(0[1-9]|1[0-2])$/, 'expected YYYY-MM')
export type YearMonth = z.infer<typeof YearMonthSchema>

/**
 * Seniority del rol de una experience. 5 niveles ordenados de menor a mayor.
 *
 * - `intern`: pasantia / practica academica
 * - `junior`: primeros 1-2 anos de carrera profesional
 * - `mid`: 2-4 anos, autonomia tecnica
 * - `senior`: 4+ anos, ownership tecnico, mentoria
 * - `lead`: people management o tech lead / architect
 *
 * Habilita el filtro `?seniority=` del CV (ver docs/specs/cv-filters-query-params.md).
 */
export const SENIORITIES = [
  'intern',
  'junior',
  'mid',
  'senior',
  'lead',
] as const
export const SeniorityValueSchema = z.enum(SENIORITIES)
export type SeniorityValue = z.infer<typeof SeniorityValueSchema>

/**
 * Tipo de un project. 6 categorias.
 *
 * - `web`: aplicacion / sitio web (Astro, Vue, Next, etc.)
 * - `mobile`: aplicacion movil (nativa o hibrida)
 * - `cli`: herramienta de linea de comandos
 * - `library`: paquete reutilizable / template / boilerplate
 * - `ai`: proyectos LLM / ML / vibe coding tooling
 * - `fintech-platform`: plataforma fintech (pagos, creditos, scoring)
 *
 * Habilita el filtro `?type=` del CV (ver docs/specs/cv-filters-query-params.md).
 */
export const PROJECT_TYPES = [
  'web',
  'mobile',
  'cli',
  'library',
  'ai',
  'fintech-platform',
] as const
export const ProjectTypeValueSchema = z.enum(PROJECT_TYPES)
export type ProjectTypeValue = z.infer<typeof ProjectTypeValueSchema>

/** YYYY-MM-DD. */
export const DateSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'expected YYYY-MM-DD')

/** Bilingual string pair. */
export const BiLangSchema = z.object({
  es: z.string().min(1),
  en: z.string().min(1),
})
export type BiLang = z.infer<typeof BiLangSchema>

/** Priority por nicho (mayor = aparece primero). */
export const PriorityByNicheSchema = z.object({
  fintech: z.number().int().nonnegative().optional(),
  architect: z.number().int().nonnegative().optional(),
  leader: z.number().int().nonnegative().optional(),
  vibe: z.number().int().nonnegative().optional(),
  generic: z.number().int().nonnegative().optional(),
})
export type PriorityByNiche = z.infer<typeof PriorityByNicheSchema>

/** Stats derivados / declarados (cards de StatsBar). */
export const ProfileStatsSchema = z.object({
  yearsExperience: z.number().int().nonnegative(),
  companies: z.number().int().nonnegative(),
  countries: z.number().int().nonnegative(),
  certifications: z.number().int().nonnegative(),
})
export type ProfileStats = z.infer<typeof ProfileStatsSchema>

/** Profile (singleton). */
export const ProfileSchema = z.object({
  name: z.string().min(1),
  handle: z.string().min(1),
  headline: BiLangSchema,
  summary: BiLangSchema,
  /**
   * Ciudad y pais en formato limpio (ej. "Lima, Perú"). Se usa tal cual en
   * schema.org `PostalAddress.addressLocality` y en `llms.txt`. NO mezclar
   * con marketing copy ("disponible remoto"); para eso usar `availability`.
   */
  location: z.string().min(1),
  /**
   * Marketing copy bilingüe sobre disponibilidad (ej. "Disponible remoto
   * · zona LATAM/US"). Opcional. Display-only: se concatena al
   * `location` en hero/CV/about para señal ATS + GEO, pero NO se mete
   * en JSON-LD ni en `llms.txt`.
   */
  availability: BiLangSchema.optional(),
  contacts: z.object({
    email: z.string().email(),
    phone: z.string().optional(),
    linkedin: z.string().url(),
    github: z.string().url(),
    website: z.string().url().optional(),
  }),
  avatarUrl: z.string().url(),
  niches: z.array(NicheSchema).min(1),
  stats: ProfileStatsSchema.optional(),
})
export type Profile = z.infer<typeof ProfileSchema>

/** Experience entry. */
export const ExperienceSchema = z.object({
  slug: z.string().min(1),
  role: BiLangSchema,
  company: z.string().min(1),
  /** Pais donde se desempeño el rol (ej. "Venezuela", "Perú", "Chile"). */
  country: z.string().min(1),
  companyUrl: z.string().url().optional(),
  start: YearMonthSchema,
  end: YearMonthSchema.optional(),
  niches: z.array(NicheSchema).min(1),
  priority: PriorityByNicheSchema.default({}),
  responsibilities: z.object({
    es: z.array(z.string().min(1)).min(1),
    en: z.array(z.string().min(1)).min(1),
  }),
  achievements: z.object({
    es: z.array(z.string().min(1)),
    en: z.array(z.string().min(1)),
  }),
  skillsTechnical: z.array(z.string().min(1)),
  skillsSoft: z.array(z.string().min(1)),
  /**
   * Seniority del rol. Habilita el filtro `?seniority=` del CV.
   * Ver SENIORITIES para valores y semantica.
   */
  seniority: SeniorityValueSchema,
  /**
   * Marcador interno: la entry tiene metricas estimadas pendientes de
   * validacion. NO se renderiza — solo audita que cifras revisar.
   */
  metricsEstimated: z.boolean().default(false),
})
export type Experience = z.infer<typeof ExperienceSchema>

/** Project entry. */
export const ProjectStatusSchema = z.enum(['active', 'inactive', 'concept'])
export const ProjectSchema = z.object({
  slug: z.string().min(1),
  name: z.string().min(1),
  summary: BiLangSchema,
  description: BiLangSchema.optional(),
  url: z.string().url().optional(),
  repo: z.string().url().optional(),
  status: ProjectStatusSchema,
  niches: z.array(NicheSchema).min(1),
  priority: PriorityByNicheSchema.default({}),
  stack: z.array(z.string().min(1)),
  caseStudy: BiLangSchema.optional(),
  metrics: z.record(z.string(), z.string()).optional(),
  caseStudyDetailed: z
    .object({
      problem: BiLangSchema,
      process: BiLangSchema,
      result: BiLangSchema,
    })
    .optional(),
  isConfidential: z.boolean().default(false),
  /**
   * Tipo de proyecto. Habilita el filtro `?type=` del CV.
   * Ver PROJECT_TYPES para valores y semantica.
   */
  projectType: ProjectTypeValueSchema,
  /**
   * Marcador interno: la entry tiene metricas estimadas pendientes de
   * validacion. NO se renderiza — solo audita que cifras revisar.
   */
  metricsEstimated: z.boolean().default(false),
})
export type Project = z.infer<typeof ProjectSchema>

/** Certificate. */
export const CertificateSchema = z.object({
  slug: z.string().min(1),
  title: z.string().min(1),
  issuer: z.string().min(1),
  date: DateSchema,
  url: z.string().url(),
  niches: z.array(NicheSchema).min(1),
})
export type Certificate = z.infer<typeof CertificateSchema>

/** Publication (Medium articles). */
export const PublicationSchema = z.object({
  slug: z.string().min(1),
  title: z.string().min(1),
  platform: z.string().min(1),
  url: z.string().url(),
  date: DateSchema,
  summary: BiLangSchema,
  canonical: z.string().url().optional(),
  niches: z.array(NicheSchema).min(1),
})
export type Publication = z.infer<typeof PublicationSchema>

/** Award. */
export const AwardSchema = z.object({
  slug: z.string().min(1),
  title: BiLangSchema,
  issuer: z.string().min(1),
  date: YearMonthSchema,
  url: z.string().url().optional(),
  motivation: BiLangSchema,
  niches: z.array(NicheSchema).min(1),
})
export type Award = z.infer<typeof AwardSchema>

/** Education entry. */
export const EducationSchema = z.object({
  slug: z.string().min(1),
  institution: z.string().min(1),
  degree: BiLangSchema.optional(),
  start: z.string().regex(/^\d{4}/),
  end: z.string().regex(/^\d{4}|Actual|Present/),
  url: z.string().url().optional(),
  description: BiLangSchema,
  /**
   * Niches en los que esta entry debe aparecer. Opcional: si se omite, la
   * entry se renderiza en todos los niches (default actual). Cuando se
   * define, habilita filtrado por nicho identico a Experience/Project.
   */
  niches: z.array(NicheSchema).min(1).optional(),
})
export type Education = z.infer<typeof EducationSchema>

/** Reference. */
export const ReferenceSchema = z.object({
  slug: z.string().min(1),
  name: z.string().min(1),
  role: z.string().min(1),
  relation: BiLangSchema,
  company: z.string().min(1).optional(),
  linkedin: z.string().url(),
  /**
   * Niches en los que esta reference debe aparecer. Opcional: si se omite,
   * la reference se renderiza en todos los niches (default actual).
   */
  niches: z.array(NicheSchema).min(1).optional(),
})
export type Reference = z.infer<typeof ReferenceSchema>

/** Language proficiency. */
export const LanguageSchema = z.object({
  /**
   * Slug opcional (deriva del filename del YAML). Solo presente cuando la
   * entry vive en un archivo individual (ej. `es.yaml`, `en.yaml`).
   */
  slug: z.string().min(1).optional(),
  name: BiLangSchema,
  level: BiLangSchema,
  /**
   * Niches en los que esta entry debe aparecer. Opcional: si se omite, la
   * entry se renderiza en todos los niches (default actual).
   */
  niches: z.array(NicheSchema).min(1).optional(),
})
export type Language = z.infer<typeof LanguageSchema>

/** Skill category (grouping skills by domain). */
export const SkillCategorySchema = z.object({
  slug: z.string().min(1),
  name: BiLangSchema,
  skills: z.array(z.string().min(1)).min(1),
  kind: z.enum(['technical', 'soft']),
  niches: z.array(NicheSchema).min(1),
})
export type SkillCategory = z.infer<typeof SkillCategorySchema>

// --------------------------------------------------------------------------
// i18n — textos de UI (NO datos del CV). Una fuente de verdad para los
// strings que renderiza cada app. Cargados desde `data/i18n/*.yaml` por
// idioma (es/en). Ver `.claude/rules/yaml-data-loading.md`.
//
// Dos familias:
//   - ElementsStrings  -> labels reutilizables, identicos para las 6 apps
//   - CurriculumStrings -> textos del CV especificos por app (hero, meta)
// --------------------------------------------------------------------------

/** Item del menu de navegacion. */
export const NavItemSchema = z.object({
  /** Clave estable del item (home, experience, about, ...). */
  key: z.string().min(1),
  /** Texto visible del link. */
  label: z.string().min(1),
})
export type NavItem = z.infer<typeof NavItemSchema>

/** Strings de los componentes interactivos (form, nav, footer, theme...). */
export const ComponentsStringsSchema = z.object({
  /** Form de contacto: labels, placeholders, mensajes de validacion y status. */
  contactForm: z.object({
    labelName: z.string().min(1),
    labelEmail: z.string().min(1),
    labelCompany: z.string().min(1),
    labelRole: z.string().min(1),
    labelServiceType: z.string().min(1),
    labelBudget: z.string().min(1),
    labelTimeline: z.string().min(1),
    labelMessage: z.string().min(1),
    optionalSummary: z.string().min(1),
    serviceTypeUnset: z.string().min(1),
    serviceTypeConsulting: z.string().min(1),
    serviceTypeFulltime: z.string().min(1),
    serviceTypeContract: z.string().min(1),
    serviceTypeOther: z.string().min(1),
    budgetPlaceholder: z.string().min(1),
    timelinePlaceholder: z.string().min(1),
    submit: z.string().min(1),
    submitting: z.string().min(1),
    sentCardTitle: z.string().min(1),
    /** Usa `{date}` como marcador para la fecha de envio. */
    sentCardBody: z.string().min(1),
    sentCardRefLabel: z.string().min(1),
    sentCardResend: z.string().min(1),
    statusSuccess: z.string().min(1),
    statusInvalidFields: z.string().min(1),
    statusCaptchaMissing: z.string().min(1),
    errorEndpointMissing: z.string().min(1),
    errorCaptchaInvalid: z.string().min(1),
    errorTooManyAttempts: z.string().min(1),
    errorServer: z.string().min(1),
    errorNetwork: z.string().min(1),
    errorCaptchaLoad: z.string().min(1),
    /** Mensajes de validacion Pydantic. `{min}` / `{max}` son marcadores. */
    validationRequired: z.string().min(1),
    validationTooShort: z.string().min(1),
    validationTooLong: z.string().min(1),
    validationEmail: z.string().min(1),
    validationFormat: z.string().min(1),
    validationNotAllowed: z.string().min(1),
    validationInvalid: z.string().min(1),
  }),
  /** Footer: copyright y boton de consentimiento. `{year}` / `{name}`. */
  footer: z.object({
    copyright: z.string().min(1),
    linkedin: z.string().min(1),
    github: z.string().min(1),
    manageConsent: z.string().min(1),
  }),
  /** Navbar + drawer movil. */
  nav: z.object({
    openMenu: z.string().min(1),
    closeMenu: z.string().min(1),
    mainMenu: z.string().min(1),
    /** Texto del switch de idioma hacia el OTRO locale. */
    switchToOtherLocale: z.string().min(1),
  }),
  /** Theme toggle: aria-labels de los 3 estados. */
  themeToggle: z.object({
    system: z.string().min(1),
    dark: z.string().min(1),
    light: z.string().min(1),
  }),
  /** Banner de cookies / consentimiento. */
  cookieBanner: z.object({
    ariaLabel: z.string().min(1),
    bodyLead: z.string().min(1),
    bodyStrong: z.string().min(1),
    bodyTail: z.string().min(1),
    accept: z.string().min(1),
    reject: z.string().min(1),
  }),
  /** Links de contacto con boton "copiar email". */
  contactLinks: z.object({
    emailLabel: z.string().min(1),
    enableJs: z.string().min(1),
    copyEmail: z.string().min(1),
    copied: z.string().min(1),
    copyFailed: z.string().min(1),
    linkedin: z.string().min(1),
    github: z.string().min(1),
  }),
  /** Chips de filtrado del CV + mensajes de lista vacia. */
  filters: z.object({
    bar: z.string().min(1),
    clear: z.string().min(1),
    tech: z.string().min(1),
    seniority: z.string().min(1),
    type: z.string().min(1),
    confidential: z.string().min(1),
    skillsTechnical: z.string().min(1),
    skillsSoft: z.string().min(1),
    emptyExperiences: z.string().min(1),
    emptyProjects: z.string().min(1),
  }),
  /** Pagina de contacto: encabezado + fallback. `{email}` es marcador. */
  contactPage: z.object({
    heading: z.string().min(1),
    intro: z.string().min(1),
    otherChannels: z.string().min(1),
    fallback: z.string().min(1),
  }),
  /** Layout base. */
  layout: z.object({
    skipToContent: z.string().min(1),
  }),
})
export type ComponentsStrings = z.infer<typeof ComponentsStringsSchema>

/** Meta de una pagina secundaria: prefijo del <title> + meta description. */
export const PageMetaSchema = z.object({
  titlePrefix: z.string().min(1),
  description: z.string().min(1),
})

/** Meta i18n de las paginas secundarias (about / certificates / contact). */
export const PagesStringsSchema = z.object({
  about: PageMetaSchema,
  certificates: PageMetaSchema,
  contact: PageMetaSchema,
})
export type PagesStrings = z.infer<typeof PagesStringsSchema>

/**
 * Strings de "elementos": labels reutilizables identicos para las 6 apps
 * (nav, stats, titulos de seccion del CV, labels genericos, componentes).
 */
export const ElementsStringsSchema = z.object({
  nav: z.array(NavItemSchema).min(1),
  stats: z.object({
    eyebrow: z.string().min(1),
    yearsExperience: z.string().min(1),
    companies: z.string().min(1),
    countries: z.string().min(1),
    certifications: z.string().min(1),
  }),
  sections: z.object({
    experience: z.object({ title: z.string().min(1) }),
    projects: z.object({ title: z.string().min(1) }),
    skills: z.object({ title: z.string().min(1) }),
    about: z.object({ title: z.string().min(1) }),
    contact: z.object({ title: z.string().min(1) }),
    certificates: z.object({ title: z.string().min(1) }),
    publications: z.object({ title: z.string().min(1) }),
    awards: z.object({ title: z.string().min(1) }),
    education: z.object({ title: z.string().min(1) }),
    languages: z.object({ title: z.string().min(1) }),
    references: z.object({ title: z.string().min(1) }),
  }),
  labels: z.object({
    home: z.string().min(1),
    downloadCv: z.string().min(1),
    viewAllExperience: z.string().min(1),
    confidential: z.string().min(1),
    technicalSkills: z.string().min(1),
    softSkills: z.string().min(1),
    responsibilities: z.string().min(1),
    achievements: z.string().min(1),
    caseStudyCta: z.string().min(1),
    caseStudyProblem: z.string().min(1),
    caseStudyProcess: z.string().min(1),
    caseStudyResult: z.string().min(1),
    caseStudyMetrics: z.string().min(1),
    ctaPrimary: z.string().min(1),
    ctaSecondary: z.string().min(1),
  }),
  components: ComponentsStringsSchema,
  pages: PagesStringsSchema,
})
export type ElementsStrings = z.infer<typeof ElementsStringsSchema>

/**
 * Strings del "curriculum": textos del CV especificos por app. El archivo
 * `_base` declara todas las claves; cada `<app>` puede omitir las que no
 * cambia (merge con fallback al base).
 */
export const CurriculumSectionOverridesSchema = z.object({
  experienceSubtitle: z.string().min(1),
  projectsSubtitle: z.string().min(1),
  skillsSubtitle: z.string().min(1),
  contactSubtitle: z.string().min(1),
  certificatesSubtitle: z.string().min(1),
  awardsSubtitle: z.string().min(1),
})

/** Forma completa del curriculum (la que produce `_base` + merge). */
export const CurriculumStringsSchema = z.object({
  meta: z.object({
    title: z.string().min(1),
    description: z.string().min(1),
  }),
  hero: z.object({
    eyebrow: z.string().min(1),
    headline: z.string().min(1),
    summary: z.string().min(1),
    nicheLabel: z.string().min(1),
  }),
  sections: CurriculumSectionOverridesSchema,
  atsKeywords: z.array(z.string().min(1)),
})
export type CurriculumStrings = z.infer<typeof CurriculumStringsSchema>

/**
 * Forma PARCIAL del curriculum: la que puede declarar un archivo `<app>`.
 * Todas las ramas son opcionales — lo ausente cae al `_base`. Solo `_base`
 * debe cumplir `CurriculumStringsSchema` completo.
 */
export const CurriculumOverrideSchema = z.object({
  meta: z
    .object({
      title: z.string().min(1).optional(),
      description: z.string().min(1).optional(),
    })
    .optional(),
  hero: z
    .object({
      eyebrow: z.string().min(1).optional(),
      headline: z.string().min(1).optional(),
      summary: z.string().min(1).optional(),
      nicheLabel: z.string().min(1).optional(),
    })
    .optional(),
  sections: CurriculumSectionOverridesSchema.partial().optional(),
  atsKeywords: z.array(z.string().min(1)).optional(),
})
export type CurriculumOverride = z.infer<typeof CurriculumOverrideSchema>

/** Card del selector del hub: titulo + blurb por niche. */
export const HubSelectorCardSchema = z.object({
  /** Niche al que apunta la card (la URL se deriva de SITE_URLS). */
  niche: NicheSchema,
  title: z.string().min(1),
  blurb: z.string().min(1),
})
export type HubSelectorCard = z.infer<typeof HubSelectorCardSchema>

/**
 * Strings exclusivos del selector multi-niche de la app `hub`. El hub no
 * renderiza `CvSections` (no usa `ElementsStrings`), por eso sus textos del
 * landing viven en un archivo i18n propio (`data/i18n/hub-selector/`).
 */
export const HubSelectorStringsSchema = z.object({
  /** Eyebrow del hero del selector. */
  heroEyebrow: z.string().min(1),
  /**
   * Mega-headline del hero, partido en 3 segmentos visuales: el primero va
   * con gradiente, el ultimo atenuado. El render concatena los 3.
   */
  heroHeadline: z.object({
    lead: z.string().min(1),
    mid: z.string().min(1),
    tail: z.string().min(1),
  }),
  /** Parrafo introductorio del hero. */
  heroIntro: z.string().min(1),
  /** Etiqueta CTA de cada card del selector ("Entrar" / "Enter"). */
  cardCta: z.string().min(1),
  /** Texto del link al otro idioma ("English version →"). */
  otherLocaleLink: z.string().min(1),
  /** Las 5 cards del selector, en orden de render. */
  cards: z.array(HubSelectorCardSchema).min(1),
})
export type HubSelectorStrings = z.infer<typeof HubSelectorStringsSchema>
