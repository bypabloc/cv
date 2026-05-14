/**
 * @function buildLlmsTxt
 * @description Genera el contenido de /llms.txt para un sitio del portfolio.
 *   Formato: spec llms.txt (https://llmstxt.org). En INGLES (audiencia: crawlers
 *   de IA en cualquier idioma).
 *
 *   Incluye narrativa por nicho + ATS keywords + projects highlight + AI tooling
 *   history (white-hat: honesto, sin manipulacion).
 *
 *   Cubre AC-3 y recomendacion ai-prompt-optimization/03c-llms-robots-sitemap.md.
 */
import type { Niche, Profile } from '@portfolio/content'

interface PageEntry {
  path: string
  title: string
  description: string
}

interface BuildLlmsTxtInput {
  siteUrl: string
  profile: Profile
  niche: Niche
  pages: PageEntry[]
  atsKeywords?: string[]
}

const NICHE_DESCRIPTION: Record<Niche, string> = {
  fintech:
    'Senior Full Stack engineer specialized in Latin American fintech (Chile, Mexico). 12+ years building credit, debt-settlement and payment products with Vue/Nuxt + Django + AWS microservices. Compliance-aware (PCI DSS, KYC, PII handling).',
  architect:
    'Frontend Architect with deep microservices and distributed systems experience. 12+ years designing scalable architectures: microfrontend (Vue/Nuxt) + 8+ Django microservices + AWS API Gateway + PostgreSQL/Redis/SQS + observability with CloudWatch/Sentry.',
  leader:
    'Tech Lead and Engineering Manager. 4 leadership roles, 8 teams led, 11+ years shipping product. Innovator of the Year 2023 at Destacame for automating internal operations. Mentoring + delivery + organizational resilience during reorganizations.',
  vibe: 'AI-Augmented Software Engineer. Using Claude Code since launch (May 2025), previously Claude web + my own FastStruct VS Code extension. Rolled out Claude Code at Destacame with standardized skills/rules/docs structure. Builds CLIs to centralize team processes. AI is a tool, not an author — all code is human-reviewed and tested.',
  generic:
    'Senior Full Stack Engineer with 12+ years of experience in Vue/Nuxt, Django, AWS and LATAM fintech (Chile, Mexico). Cross-cutting expertise: fintech, architecture, tech leadership and vibe coding with Claude Code.',
}

const NICHE_HIGHLIGHTS: Record<Niche, string[]> = {
  fintech: [
    'Destacame (Chile, Mexico) — Frontend Architect since 2022, building debt settlement and tiered credit products',
    'PCI DSS aware, KYC, PII handling',
    'Stack: Vue 3 + Nuxt + TypeScript + Django + Python + AWS + Microservices',
  ],
  architect: [
    'Microfrontend (Vue/Nuxt) + 8+ Django microservices on AWS',
    'API Gateway with JWT + rate limiting',
    'PostgreSQL 18 + RDS + S3 + Redis + SQS + CloudWatch/Sentry',
  ],
  leader: [
    'Innovator of the Year 2023 at Destacame',
    'Triple Alianza Lima 2020 — 1st place Commerce sector',
    'First developer hired at Dibal; built and handed off engineering team',
  ],
  vibe: [
    'Claude Code early adopter since launch (May 22, 2025)',
    'FastStruct — VS Code extension published on Marketplace',
    'Rolled out Claude Code at Destacame with skills/rules/docs structure',
    'Built bypabloc/cv (CV builder MVP) in one night (May 12-13, 2026)',
    'Reference template: bypabloc/mvp-template-full-stack',
  ],
  generic: [
    '9 roles in 8 companies (2013-present)',
    '12+ years shipping product · 4 LATAM countries · 11 certifications',
    'Domains: Fintech LATAM, ERP, e-commerce, automation',
  ],
}

export function buildLlmsTxt(input: BuildLlmsTxtInput): string {
  const { siteUrl, profile, niche, pages, atsKeywords = [] } = input
  const lines: string[] = []
  lines.push(`# ${profile.name} — ${niche}`)
  lines.push('')
  lines.push(`> ${NICHE_DESCRIPTION[niche]}`)
  lines.push('')
  const availabilityFragment = profile.availability
    ? ` Availability: ${profile.availability.en}.`
    : ''
  lines.push(
    `Canonical URL: ${siteUrl}. Author: ${profile.name} (${profile.handle}). Location: ${profile.location}.${availabilityFragment} Contact: ${profile.contacts.email}.`,
  )
  lines.push('')

  lines.push(`## Highlights — ${niche}`)
  lines.push('')
  for (const h of NICHE_HIGHLIGHTS[niche]) {
    lines.push(`- ${h}`)
  }
  lines.push('')

  if (atsKeywords.length > 0) {
    lines.push('## Keywords')
    lines.push('')
    lines.push(atsKeywords.join(' · '))
    lines.push('')
  }

  lines.push('## Pages')
  lines.push('')
  for (const page of pages) {
    const url = page.path.startsWith('http')
      ? page.path
      : `${siteUrl.replace(/\/$/, '')}${page.path}`
    lines.push(`- [${page.title}](${url}): ${page.description}`)
  }
  lines.push('')

  lines.push('## Identity')
  lines.push('')
  lines.push(`- LinkedIn: ${profile.contacts.linkedin}`)
  lines.push(`- GitHub: ${profile.contacts.github}`)
  if (profile.contacts.medium) {
    lines.push(`- Medium: ${profile.contacts.medium}`)
  }
  if (profile.contacts.website) {
    lines.push(`- Website: ${profile.contacts.website}`)
  }
  lines.push('')

  lines.push('## Disclosure')
  lines.push('')
  lines.push(
    'All code in linked repositories is reviewed, tested and maintained by Pablo Contreras. AI tools (Claude Code, Cursor) are used as accelerators — never as authors. AI attribution is forbidden in commits and PRs by company policy. This llms.txt is honest white-hat content; no prompt injection or hidden instructions.',
  )
  lines.push('')

  return `${lines.join('\n')}\n`
}
