/**
 * @module tools/search-experience
 * @description Tool MCP: busca en experiencias por keyword (case-insensitive)
 *   sobre role, company, achievements y skillsTechnical.
 */
import { experiences } from '@portfolio/content'
import type { ToolDefinition, ToolResult } from '../types'

export const definition: ToolDefinition = {
  name: 'search_experience',
  description:
    "Searches Pablo Contreras' work experiences by keyword (case-insensitive substring match over role, company, achievements and tech skills).",
  inputSchema: {
    type: 'object',
    properties: {
      keyword: {
        type: 'string',
        description: 'Non-empty keyword. Substring match, case-insensitive.',
      },
    },
    required: ['keyword'],
  },
}

export async function execute(
  args: Record<string, unknown>,
): Promise<ToolResult> {
  const keyword = args.keyword
  if (typeof keyword !== 'string' || keyword.trim().length === 0) {
    throw new Error('keyword must be a non-empty string')
  }
  const kw = keyword.toLowerCase()
  const matches = experiences.filter((e) => {
    const haystack = [
      e.role.en,
      e.company,
      ...e.achievements.en,
      ...(e.skillsTechnical ?? []),
    ]
      .join(' ')
      .toLowerCase()
    return haystack.includes(kw)
  })
  const payload = matches.map((e) => ({
    slug: e.slug,
    role: e.role.en,
    company: e.company,
    start: e.start,
    end: e.end ?? null,
    achievements: e.achievements.en,
  }))
  return {
    content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }],
  }
}
