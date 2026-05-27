/**
 * @description Tests para buildMcpServerCard — JSON publicado en
 *   /.well-known/mcp/server-card.json. Validado por isitagentready.com.
 */
import { describe, expect, it } from 'vitest'

import { buildMcpServerCard } from '../../src/lib/build-mcp-server-card'

describe('buildMcpServerCard', () => {
  it('Given siteUrl When build Then devuelve JSON valido con campos MCP', () => {
    const out = buildMcpServerCard({
      siteUrl: 'https://the-full-stack.com',
    })

    const parsed = JSON.parse(out) as Record<string, unknown>
    expect(parsed.name).toBe('portfolio-mcp')
    expect(parsed.version).toBe('0.1.0')
    expect(parsed.protocolVersion).toBe('2025-11-25')
    expect(parsed.endpoint).toBe('https://the-full-stack.com/mcp')
    expect(parsed.transport).toBe('http')
  })

  it('Given siteUrl con trailing slash When build Then strip + endpoint correcto', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://x.com/' })

    const parsed = JSON.parse(out) as { endpoint: string }
    expect(parsed.endpoint).toBe('https://x.com/mcp')
  })

  it('Given build When inspect Then capabilities.tools.listChanged=false', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://x.com' })

    const parsed = JSON.parse(out) as {
      capabilities: { tools: { listChanged: boolean } }
    }
    expect(parsed.capabilities.tools.listChanged).toBe(false)
  })

  it('Given build When inspect Then tools array contiene los 3 tools del portfolio', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://x.com' })

    const parsed = JSON.parse(out) as { tools: Array<{ name: string }> }
    expect(parsed.tools.map((t) => t.name)).toEqual([
      'get_cv_section',
      'list_projects',
      'search_experience',
    ])
  })

  it('Given se invoca When inspecciono Then termina con newline (req editores)', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://x.com' })

    expect(out.endsWith('\n')).toBe(true)
  })

  it('Given build When inspect Then cada tool tiene inputSchema valido', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://x.com' })

    const parsed = JSON.parse(out) as {
      tools: Array<{ name: string; inputSchema: { type: string } }>
    }
    for (const tool of parsed.tools) {
      expect(tool.inputSchema.type).toBe('object')
    }
  })
})
