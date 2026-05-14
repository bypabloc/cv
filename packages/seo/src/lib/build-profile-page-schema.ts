/**
 * @function buildProfilePageSchema
 * @description Construye un schema.org ProfilePage que envuelve un Person.
 *   ProfilePage es el tipo recomendado para portfolios personales (vs solo
 *   Person en un WebPage genérico) — mejora GEO en ChatGPT/Claude/Perplexity.
 *
 *   Recomendado por modern-portfolios/03-geo-llm-seo.md +
 *   ai-prompt-optimization/03a-json-ld-schemas.md.
 *
 * @param input - profile, niche, locale, canonicalUrl, knowsAbout
 * @returns JSON-LD stringificado del ProfilePage (con Person embebido)
 *
 * @example
 *   const ld = buildProfilePageSchema({
 *     profile, niche: 'fintech', locale: 'es',
 *     canonicalUrl: 'https://fintech.the-full-stack.com/',
 *     knowsAbout: ['Vue', 'Django']
 *   })
 */
import type { Niche, Profile } from '@portfolio/content'

interface BuildProfilePageSchemaInput {
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
    es: 'Ingeniero de Software AI-Augmented (Claude Code, Cursor)',
    en: 'AI-Augmented Software Engineer (Claude Code, Cursor)',
  },
  generic: {
    es: 'Ingeniero de Software Full Stack senior',
    en: 'Senior Full Stack Software Engineer',
  },
}

export function buildProfilePageSchema(
  input: BuildProfilePageSchemaInput,
): string {
  const { profile, niche, locale, canonicalUrl, knowsAbout } = input
  const jobTitle = JOB_TITLE_BY_NICHE[niche][locale]
  const description = profile.summary[locale]

  const sameAs = [profile.contacts.linkedin, profile.contacts.github]
  if (profile.contacts.medium) {
    sameAs.push(profile.contacts.medium)
  }
  if (profile.contacts.website) {
    sameAs.push(profile.contacts.website)
  }

  const ld = {
    '@context': 'https://schema.org',
    '@type': 'ProfilePage',
    dateModified: new Date().toISOString().split('T')[0],
    mainEntity: {
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
      hasOccupation: {
        '@type': 'Occupation',
        name: jobTitle,
        occupationLocation: [
          {
            '@type': 'Country',
            name: locale === 'es' ? 'Perú' : 'Peru',
          },
          {
            '@type': 'VirtualLocation',
            name:
              locale === 'es'
                ? 'Remoto · zona horaria LATAM/US'
                : 'Remote · LATAM/US timezone',
          },
        ],
        skills: knowsAbout.join(', '),
      },
      seeks: {
        '@type': 'Demand',
        name:
          locale === 'es'
            ? 'Roles full stack senior remotos (LATAM/US)'
            : 'Remote senior full stack roles (LATAM/US)',
      },
    },
  }

  return JSON.stringify(ld)
}
