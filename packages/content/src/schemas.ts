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
  location: z.string().min(1),
  contacts: z.object({
    email: z.string().email(),
    phone: z.string().optional(),
    linkedin: z.string().url(),
    github: z.string().url(),
    medium: z.string().url().optional(),
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
})
export type Reference = z.infer<typeof ReferenceSchema>

/** Language proficiency. */
export const LanguageSchema = z.object({
  name: BiLangSchema,
  level: BiLangSchema,
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
