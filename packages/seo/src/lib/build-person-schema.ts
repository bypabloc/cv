/**
 * @function buildPersonSchema
 * @description Construye un schema.org Person para JSON-LD. Toma el Profile
 *   compartido y ajusta jobTitle/knowsAbout/description al nicho.
 *
 *   Cubre AC-2: cada subdominio tiene JSON-LD Person valido con campos
 *   especificos del nicho.
 *
 * @param input - profile, niche, locale, canonicalUrl, knowsAbout (skills filtradas)
 * @returns JSON-LD stringificado (listo para <script type="application/ld+json">)
 *
 * @example
 *   const ld = buildPersonSchema({
 *     profile,
 *     niche: 'fintech',
 *     locale: 'en',
 *     canonicalUrl: 'https://fintech.the-full-stack.com/',
 *     knowsAbout: ['Vue', 'Django', 'AWS', 'Fintech'],
 *   })
 *   //  '{"@context":"https://schema.org","@type":"Person",...}'
 */
import type { Niche, Profile } from '@portfolio/content'

interface BuildPersonSchemaInput {
  profile: Profile
  niche: Niche
  locale: 'es' | 'en'
  canonicalUrl: string
  knowsAbout: string[]
}

const JOB_TITLE_BY_NICHE: Record<Niche, { es: string; en: string }> = {
  fintech: {
    es: 'Ingeniero Full Stack senior — Fintech LATAM',
    en: 'Senior Full Stack Engineer — LATAM Fintech',
  },
  architect: {
    es: 'Arquitecto de Software y Microservicios',
    en: 'Software and Microservices Architect',
  },
  leader: {
    es: 'Tech Lead / Engineering Manager',
    en: 'Tech Lead / Engineering Manager',
  },
  vibe: {
    es: 'Ingeniero de Software con workflows de IA (Claude Code, Cursor)',
    en: 'Software Engineer with AI workflows (Claude Code, Cursor)',
  },
  generic: {
    es: 'Ingeniero de Software Full Stack senior',
    en: 'Senior Full Stack Software Engineer',
  },
}

interface PersonLd {
  '@context': 'https://schema.org'
  '@type': 'Person'
  name: string
  alternateName?: string
  jobTitle: string
  description: string
  url: string
  email: string
  image?: string
  address: { '@type': 'PostalAddress'; addressLocality: string }
  sameAs: string[]
  knowsAbout: string[]
}

export function buildPersonSchema(input: BuildPersonSchemaInput): string {
  const { profile, niche, locale, canonicalUrl, knowsAbout } = input
  const jobTitle = JOB_TITLE_BY_NICHE[niche][locale]
  const description = profile.summary[locale]

  const sameAs = [profile.contacts.linkedin, profile.contacts.github]
  if (profile.contacts.medium) sameAs.push(profile.contacts.medium)
  if (profile.contacts.website) sameAs.push(profile.contacts.website)

  const ld: PersonLd = {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: profile.name,
    alternateName: profile.handle,
    jobTitle,
    description,
    url: canonicalUrl,
    email: profile.contacts.email,
    image: profile.avatarUrl,
    address: {
      '@type': 'PostalAddress',
      addressLocality: profile.location,
    },
    sameAs,
    knowsAbout,
  }

  return JSON.stringify(ld)
}
