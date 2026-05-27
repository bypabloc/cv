/**
 * @module build-mcp-server-card
 * @description Genera el JSON del archivo `/.well-known/mcp/server-card.json`
 *   que describe el MCP server del portfolio (endpoint POST /mcp con sus
 *   3 tools). isitagentready.com lo lee como parte del check "MCP Server
 *   Card not found"; agentes lo usan para auto-descubrir el endpoint
 *   y las tools disponibles.
 *
 *   Schema basado en la spec modelcontextprotocol.io (2025-11-25).
 */
import { PROTOCOL_VERSION, TOOLS } from '@portfolio/mcp'

interface ServerCardParams {
  /** URL absoluta del sitio. Ej: 'https://the-full-stack.com'. */
  siteUrl: string
}

/**
 * @function buildMcpServerCard
 * @description Devuelve el JSON ya stringificado listo para escribirse
 *   en `public/.well-known/mcp/server-card.json`. Termina con newline.
 *
 * @example
 *   buildMcpServerCard({ siteUrl: 'https://the-full-stack.com' })
 *   // '{\n  "name": "portfolio-mcp", ... }\n'
 */
export function buildMcpServerCard(params: ServerCardParams): string {
  const baseUrl = stripTrailingSlash(params.siteUrl)
  const card = {
    name: 'portfolio-mcp',
    version: '0.1.0',
    protocolVersion: PROTOCOL_VERSION,
    description: "Pablo Contreras' portfolio MCP server — CV exploration tools",
    endpoint: `${baseUrl}/mcp`,
    transport: 'http',
    capabilities: { tools: { listChanged: false } },
    tools: TOOLS.map((t) => t.definition),
  }
  return `${JSON.stringify(card, null, 2)}\n`
}

function stripTrailingSlash(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url
}
