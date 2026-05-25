/**
 * @module cv-api-client
 * @description Cliente HTTP del API `cv` del backend serverless.
 *
 *   El backend `GET /cv` expone el CV en formato relacional (traducciones
 *   como `{es, en}` por campo, responsabilidades como array de bullets
 *   bilingues). Este cliente pega al API y devuelve la respuesta tipada.
 *
 *   IMPORTANTE: el shape de la respuesta del API NO coincide 1:1 con los
 *   Zod schemas historicos de `@portfolio/content` (esos modelaban YAML
 *   estatico). El cliente expone los tipos de respuesta del API tal cual;
 *   los consumidores (prebuild de las apps Astro) se adaptan al nuevo
 *   shape. La migracion 1:1 de TODOS los componentes Astro queda fuera
 *   del scope del plan c-cv-data-service (ver TODO de la Fase D).
 *
 * @example
 *   const cv = await fetchCv({ niche: 'fintech', locale: 'es' })
 *   cv.profile.name // 'Pablo Contreras'
 *   cv.experiences[0].role.es // 'Arquitecto Frontend ...'
 */

/** Texto bilingue: `{es, en}` por campo. Vacio si la entidad no traduce. */
export type BiLangText = Partial<Record<'es' | 'en', string>>

/** Niche valido del portfolio. */
export type CvNiche = 'fintech' | 'architect' | 'leader' | 'vibe' | 'generic'

export type CvLocale = 'es' | 'en'

export interface CvProfile {
  slug: string
  name: string
  handle: string
  location: string
  avatarUrl: string
  contacts: {
    email: string
    phone: string | null
    linkedin: string
    github: string
    website: string | null
  }
  headline: BiLangText
  summary: BiLangText
  availability: BiLangText
  niches: CvNiche[]
  stats?: {
    yearsExperience: number
    companies: number
    countries: number
    certifications: number
  }
}

export interface CvExperience {
  slug: string
  company: string
  country: string
  companyUrl: string | null
  start: string
  end: string | null
  seniority: string
  metricsEstimated: boolean
  role: BiLangText
  responsibilities: BiLangText[]
  achievements: BiLangText[]
  priority?: number
}

export interface CvProject {
  slug: string
  name: string
  url: string | null
  repo: string | null
  status: string
  projectType: string
  isConfidential: boolean
  metricsEstimated: boolean
  summary: BiLangText
  description: BiLangText
  caseStudy: BiLangText
  stack: string[]
  metrics: Record<string, string>
  caseStudyDetailed?: {
    problem: BiLangText
    process: BiLangText
    result: BiLangText
  }
  priority?: number
}

export interface CvCertificate {
  slug: string
  title: string
  issuer: string
  date: string | null
  url: string
}

export interface CvAward {
  slug: string
  issuer: string
  date: string
  url: string | null
  title: BiLangText
  motivation: BiLangText
}

export interface CvEducation {
  slug: string
  institution: string
  start: string
  end: string
  url: string | null
  degree: BiLangText
  description: BiLangText
}

export interface CvLanguage {
  slug: string
  name: BiLangText
  level: BiLangText
}

export interface CvReference {
  slug: string
  name: string
  role: string
  company: string | null
  linkedin: string
  relation: BiLangText
}

export interface CvSkillCategory {
  slug: string
  kind: string
  name: BiLangText
  skills: string[]
}

export interface CvFull {
  profile: CvProfile | Record<string, never>
  experiences: CvExperience[]
  projects: CvProject[]
  certificates: CvCertificate[]
  awards: CvAward[]
  education: CvEducation[]
  languages: CvLanguage[]
  references: CvReference[]
  skillCategories: CvSkillCategory[]
}

export interface CvFetchOptions {
  /** Filtro por niche. Sin niche -> sin filtro (toda la coleccion). */
  niche?: CvNiche
  /** Locale para textos bilingues. Default 'es'. */
  locale?: CvLocale
  /** Base URL del API (override de la env var PUBLIC_CV_API_URL). */
  apiBase?: string
}

/**
 * Resuelve la URL base del API desde `apiBase` explicito o
 * `PUBLIC_CV_API_URL` / `CV_API_URL` del entorno.
 */
function resolveApiBase(explicit?: string): string {
  if (explicit) return explicit
  const env =
    typeof process !== 'undefined' && process.env
      ? process.env
      : ({} as Record<string, string | undefined>)
  const base = env.PUBLIC_CV_API_URL ?? env.CV_API_URL
  if (!base) {
    throw new Error(
      'cv-api-client: ni `apiBase` ni `PUBLIC_CV_API_URL`/`CV_API_URL` estan' +
        ' definidos. Setea la env var del API antes del prebuild.',
    )
  }
  return base
}

async function callCv<T>(
  action: string,
  options: CvFetchOptions | undefined,
): Promise<T> {
  const apiBase = resolveApiBase(options?.apiBase).replace(/\/+$/, '')
  const params = new URLSearchParams({ operation: 'cv', action })
  if (options?.niche) params.set('niche', options.niche)
  params.set('locale', options?.locale ?? 'es')

  const url = `${apiBase}/cv?${params.toString()}`
  const res = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) {
    throw new Error(
      `cv-api-client: ${url} respondio HTTP ${res.status} ${res.statusText}`,
    )
  }
  return (await res.json()) as T
}

/** GET /cv?action=get — CV completo. */
export function fetchCv(options?: CvFetchOptions): Promise<CvFull> {
  return callCv<CvFull>('get', options)
}

/** GET /cv?action=profile — profile + stats. */
export function fetchProfile(
  options?: CvFetchOptions,
): Promise<CvProfile | Record<string, never>> {
  return callCv<CvProfile | Record<string, never>>('profile', options)
}

/** GET /cv?action=experiences — experiencias filtradas por niche. */
export function fetchExperiences(
  options?: CvFetchOptions,
): Promise<CvExperience[]> {
  return callCv<CvExperience[]>('experiences', options)
}

/** GET /cv?action=projects — proyectos filtrados por niche. */
export function fetchProjects(options?: CvFetchOptions): Promise<CvProject[]> {
  return callCv<CvProject[]>('projects', options)
}

/** GET /cv?action=certificates — certificados. */
export function fetchCertificates(
  options?: CvFetchOptions,
): Promise<CvCertificate[]> {
  return callCv<CvCertificate[]>('certificates', options)
}

/** GET /cv?action=awards — premios. */
export function fetchAwards(options?: CvFetchOptions): Promise<CvAward[]> {
  return callCv<CvAward[]>('awards', options)
}

/** GET /cv?action=education — educacion. */
export function fetchEducation(
  options?: CvFetchOptions,
): Promise<CvEducation[]> {
  return callCv<CvEducation[]>('education', options)
}

/** GET /cv?action=languages — idiomas. */
export function fetchLanguages(
  options?: CvFetchOptions,
): Promise<CvLanguage[]> {
  return callCv<CvLanguage[]>('languages', options)
}

/** GET /cv?action=references — referencias. */
export function fetchReferences(
  options?: CvFetchOptions,
): Promise<CvReference[]> {
  return callCv<CvReference[]>('references', options)
}

/** GET /cv?action=skills — categorias de skills. */
export function fetchSkillCategories(
  options?: CvFetchOptions,
): Promise<CvSkillCategory[]> {
  return callCv<CvSkillCategory[]>('skills', options)
}
