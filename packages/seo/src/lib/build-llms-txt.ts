/**
 * @function buildLlmsTxt
 * @description Genera el contenido de /llms.txt para un sitio del portfolio.
 *   Formato: spec llms.txt (https://llmstxt.org). En INGLES (audiencia: crawlers
 *   de IA en cualquier idioma).
 *
 *   Cubre AC-3: cada subdominio sirve llms.txt con páginas y resumenes.
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
}

const NICHE_DESCRIPTION: Record<Niche, string> = {
  fintech:
    'Senior Full Stack engineer specialized in Latin American fintech (Chile, Mexico). 8+ years building credit, debt-settlement and payment products with Vue/Nuxt + Django + AWS microservices.',
  architect:
    'Frontend Architect with deep microservices experience. 8+ years designing scalable systems with Vue/Nuxt, Django, AWS and microfrontends.',
  leader:
    'Tech Lead with experience leading multi-disciplinary engineering teams, mentoring junior developers and shipping fintech products at scale.',
  vibe: 'Software engineer who documents real workflows with Claude Code and Cursor. Builds developer tools (VS Code extensions, monorepo automation) and shares prompts that ship.',
  generic:
    'Senior Full Stack Engineer with 8+ years of experience in Vue/Nuxt, Django, AWS and fintech (Chile, Mexico).',
}

export function buildLlmsTxt(input: BuildLlmsTxtInput): string {
  const { siteUrl, profile, niche, pages } = input
  const lines: string[] = []
  lines.push(`# ${profile.name} — ${niche}`)
  lines.push('')
  lines.push(`> ${NICHE_DESCRIPTION[niche]}`)
  lines.push('')
  lines.push(
    `Canonical URL: ${siteUrl}. Author: ${profile.name} (${profile.handle}). Location: ${profile.location}. Contact: ${profile.contacts.email}.`,
  )
  lines.push('')
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
  lines.push('')
  return `${lines.join('\n')}\n`
}
