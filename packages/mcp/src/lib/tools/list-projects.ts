/**
 * @module tools/list-projects
 * @description Tool MCP: lista los proyectos del CV, opcionalmente
 *   filtrados por keyword en el stack.
 */
import { projects } from '@portfolio/content'
import type { ToolDefinition, ToolResult } from '../types'

export const definition: ToolDefinition = {
  name: 'list_projects',
  description:
    "Lists Pablo Contreras' projects, optionally filtered by a tech stack keyword (case-insensitive substring match).",
  inputSchema: {
    type: 'object',
    properties: {
      tech_stack: {
        type: 'string',
        description:
          'Optional filter (case-insensitive substring) applied to each project stack entry. Ex: "Astro", "AWS", "Vue".',
      },
    },
  },
}

export async function execute(
  args: Record<string, unknown>,
): Promise<ToolResult> {
  const raw = args.tech_stack
  const filter =
    typeof raw === 'string' && raw.trim().length > 0 ? raw.toLowerCase() : null
  const filtered = filter
    ? projects.filter((p) =>
        p.stack.some((s) => s.toLowerCase().includes(filter)),
      )
    : [...projects]
  const payload = filtered.map((p) => ({
    slug: p.slug,
    name: p.name,
    summary: p.summary.en,
    stack: p.stack,
    url: p.url ?? null,
  }))
  return {
    content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }],
  }
}
