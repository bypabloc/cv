/**
 * @module build-agent-skills
 * @description Genera el JSON del archivo `/.well-known/agent-skills/index.json`
 *   (agent skills discovery index) que lista las skills del agente del
 *   portfolio con su nombre, tipo, descripcion, URL y digest.
 *
 *   isitagentready.com lo lee como el check "Agent Skills index"; un agente
 *   externo lo usa para enumerar las capacidades disponibles. Las skills
 *   se DERIVAN de los 3 MCP tools de `@portfolio/mcp` (fuente unica de
 *   verdad, igual que el server card y el agent card).
 */
import { TOOLS } from '@portfolio/mcp'

interface AgentSkillsParams {
  /** URL absoluta del sitio. Ej: 'https://the-full-stack.com'. */
  siteUrl: string
}

/**
 * @function buildAgentSkills
 * @description Devuelve el JSON del skills index stringificado, listo para
 *   inlinearse en el Worker y servirse en `/.well-known/agent-skills/index.json`.
 *   Termina con newline.
 *
 * @param {AgentSkillsParams} params
 * @returns {string} JSON con trailing newline.
 *
 * @example
 *   buildAgentSkills({ siteUrl: 'https://the-full-stack.com' })
 *   // '{\n  "skills": [ ... ] }\n'
 */
export function buildAgentSkills(params: AgentSkillsParams): string {
  const baseUrl = stripTrailingSlash(params.siteUrl)
  const index = {
    skills: TOOLS.map((t) => ({
      name: t.definition.name,
      type: 'mcp-tool',
      description: t.definition.description,
      url: `${baseUrl}/mcp`,
    })),
  }
  return `${JSON.stringify(index, null, 2)}\n`
}

function stripTrailingSlash(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url
}
