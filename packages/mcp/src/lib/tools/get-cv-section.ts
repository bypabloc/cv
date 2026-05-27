/**
 * @module tools/get-cv-section
 * @description Tool MCP: devuelve una seccion del CV en Markdown
 *   (en ingles por default). Los datos los recibe via `MCPDataProvider`
 *   inyectado por el caller (la Pages Function).
 */
import type { MCPDataProvider, ToolDefinition, ToolResult } from '../types'

const SECTIONS = [
  'about',
  'experience',
  'projects',
  'skills',
  'education',
  'contact',
] as const
type Section = (typeof SECTIONS)[number]

export const definition: ToolDefinition = {
  name: 'get_cv_section',
  description:
    "Returns a section of Pablo Contreras' CV in Markdown (about, experience, projects, skills, education or contact).",
  inputSchema: {
    type: 'object',
    properties: {
      section: {
        type: 'string',
        enum: [...SECTIONS],
        description: 'Which CV section to fetch',
      },
    },
    required: ['section'],
  },
}

export async function execute(
  args: Record<string, unknown>,
  data: MCPDataProvider,
): Promise<ToolResult> {
  const section = args.section
  if (typeof section !== 'string' || !isSection(section)) {
    throw new Error(
      `unknown section: ${String(section)}. Valid: ${SECTIONS.join(', ')}`,
    )
  }
  const text = renderSection(section, data)
  return { content: [{ type: 'text', text }] }
}

function isSection(s: string): s is Section {
  return (SECTIONS as readonly string[]).includes(s)
}

function renderSection(section: Section, data: MCPDataProvider): string {
  const profile = data.getProfile()
  switch (section) {
    case 'about':
      return [
        '# About',
        '',
        profile.summary.en,
        '',
        `**Location**: ${profile.location}`,
        `**Availability**: ${profile.availability?.en ?? 'On request'}`,
        '',
      ].join('\n')

    case 'experience':
      return [
        '# Experience',
        '',
        ...data
          .getExperiences()
          .map((e) =>
            [
              `## ${e.role.en} @ ${e.company} (${e.start} - ${e.end ?? 'Present'})`,
              '',
              e.summary?.en ?? '',
              '',
              '**Achievements**:',
              ...e.achievements.en.map((a) => `- ${a}`),
            ].join('\n'),
          ),
        '',
      ].join('\n\n')

    case 'projects':
      return [
        '# Projects',
        '',
        ...data
          .getProjects()
          .map((p) =>
            [
              `## ${p.name}`,
              '',
              p.summary.en,
              '',
              `**Stack**: ${p.stack.join(', ')}`,
              ...(p.url ? [`**URL**: ${p.url}`] : []),
            ].join('\n'),
          ),
        '',
      ].join('\n\n')

    case 'skills':
      return [
        '# Skills',
        '',
        ...data
          .getSkills()
          .map((cat) =>
            [
              `## ${cat.name.en}`,
              '',
              cat.skills.map((s) => `- ${s}`).join('\n'),
            ].join('\n'),
          ),
        '',
      ].join('\n\n')

    case 'education':
      return [
        '# Education',
        '',
        ...data.getEducation().map((ed) => {
          const label = ed.degree?.en ?? ed.institution
          return `- **${label}**, ${ed.institution} (${ed.start ?? '?'} - ${ed.end ?? 'Present'})`
        }),
        '',
      ].join('\n')

    case 'contact':
      return [
        '# Contact',
        '',
        `- **Email**: ${profile.contacts.email}`,
        `- **LinkedIn**: ${profile.contacts.linkedin}`,
        `- **GitHub**: ${profile.contacts.github}`,
        `- **Website**: ${profile.contacts.website}`,
        '',
      ].join('\n')
  }
}
