/**
 * @module build-agent-card
 * @description Genera el JSON del archivo `/.well-known/agent-card.json`
 *   (A2A Agent Card, spec a2a-protocol.org) que describe el agente del
 *   portfolio para descubrimiento agent-to-agent.
 *
 *   isitagentready.com lo lee como el check "A2A Agent Card"; un agente
 *   externo lo usa para auto-descubrir las capabilities y skills disponibles
 *   antes de hablar con el endpoint MCP (POST /mcp).
 *
 *   Las skills se DERIVAN de los 3 MCP tools de `@portfolio/mcp` (fuente
 *   unica de verdad, igual que el server card) para no duplicar la lista.
 */
import { TOOLS } from '@portfolio/mcp'

interface AgentCardParams {
  /** URL absoluta del sitio. Ej: 'https://the-full-stack.com'. */
  siteUrl: string
}

/**
 * @function buildAgentCard
 * @description Devuelve el JSON A2A Agent Card stringificado, listo para
 *   inlinearse en el Worker y servirse en `/.well-known/agent-card.json`.
 *   Termina con newline.
 *
 * @param {AgentCardParams} params
 * @returns {string} JSON con trailing newline.
 *
 * @example
 *   buildAgentCard({ siteUrl: 'https://the-full-stack.com' })
 *   // '{\n  "name": "portfolio-agent", ... }\n'
 */
export function buildAgentCard(params: AgentCardParams): string {
  const baseUrl = stripTrailingSlash(params.siteUrl)
  const card = {
    name: 'portfolio-agent',
    description:
      "Pablo Contreras' portfolio agent — read-only CV exploration over MCP.",
    version: '0.1.0',
    url: `${baseUrl}/mcp`,
    preferredTransport: 'http',
    provider: {
      organization: 'Pablo Contreras',
      url: baseUrl,
    },
    capabilities: {
      streaming: false,
      pushNotifications: false,
      stateTransitionHistory: false,
    },
    defaultInputModes: ['application/json'],
    defaultOutputModes: ['application/json', 'text/markdown'],
    skills: TOOLS.map((t) => ({
      id: t.definition.name,
      name: t.definition.name,
      description: t.definition.description,
      tags: ['cv', 'read-only'],
    })),
  }
  return `${JSON.stringify(card, null, 2)}\n`
}

function stripTrailingSlash(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url
}
