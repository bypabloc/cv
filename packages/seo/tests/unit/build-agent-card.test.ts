/**
 * @description Tests para buildAgentCard. Genera el A2A Agent Card
 *   (/.well-known/agent-card.json) con skills derivadas de los 3 MCP tools.
 */
import { TOOLS } from '@portfolio/mcp'
import { describe, expect, it } from 'vitest'

import { buildAgentCard } from '../../src/lib/build-agent-card'

describe('buildAgentCard', () => {
  it('Given siteUrl When build Then JSON valido con name, version, url al endpoint MCP', () => {
    const out = buildAgentCard({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    expect(parsed.name).toBe('portfolio-agent')
    expect(parsed.version).toBe('0.1.0')
    expect(parsed.url).toBe('https://the-full-stack.com/mcp')
    expect(parsed.preferredTransport).toBe('http')
  })

  it('Given siteUrl When build Then provider apunta al apex', () => {
    const out = buildAgentCard({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    expect(parsed.provider).toEqual({
      organization: 'Pablo Contreras',
      url: 'https://the-full-stack.com',
    })
  })

  it('Given los 3 MCP tools When build Then skills = 3, derivadas de TOOLS', () => {
    const out = buildAgentCard({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    expect(parsed.skills).toHaveLength(TOOLS.length)
    expect(parsed.skills.map((s: { id: string }) => s.id)).toEqual(
      TOOLS.map((t) => t.definition.name),
    )
  })

  it('Given una skill When inspecciono Then tiene id, name, description y tags', () => {
    const out = buildAgentCard({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    const first = parsed.skills[0]
    expect(first.id).toBe(TOOLS[0]?.definition.name)
    expect(first.name).toBe(TOOLS[0]?.definition.name)
    expect(first.description).toBe(TOOLS[0]?.definition.description)
    expect(first.tags).toEqual(['cv', 'read-only'])
  })

  it('Given capabilities When inspecciono Then streaming y push estan en false', () => {
    const out = buildAgentCard({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    expect(parsed.capabilities).toEqual({
      streaming: false,
      pushNotifications: false,
      stateTransitionHistory: false,
    })
  })

  it('Given siteUrl con trailing slash When build Then strippa la slash', () => {
    const out = buildAgentCard({ siteUrl: 'https://x.com/' })

    const parsed = JSON.parse(out)
    expect(parsed.url).toBe('https://x.com/mcp')
    expect(parsed.provider.url).toBe('https://x.com')
  })

  it('Given se invoca When inspecciono Then termina con newline', () => {
    const out = buildAgentCard({ siteUrl: 'https://x.com' })

    expect(out.endsWith('\n')).toBe(true)
  })
})
