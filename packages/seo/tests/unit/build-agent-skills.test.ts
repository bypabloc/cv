/**
 * @description Tests para buildAgentSkills. Genera el skills discovery index
 *   (/.well-known/agent-skills/index.json) derivado de los 3 MCP tools.
 */
import { TOOLS } from '@portfolio/mcp'
import { describe, expect, it } from 'vitest'

import { buildAgentSkills } from '../../src/lib/build-agent-skills'

describe('buildAgentSkills', () => {
  it('Given los 3 MCP tools When build Then skills = 3, derivadas de TOOLS', () => {
    const out = buildAgentSkills({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    expect(parsed.skills).toHaveLength(TOOLS.length)
    expect(parsed.skills.map((s: { name: string }) => s.name)).toEqual(
      TOOLS.map((t) => t.definition.name),
    )
  })

  it('Given una skill When inspecciono Then tiene name, type, description y url al endpoint MCP', () => {
    const out = buildAgentSkills({ siteUrl: 'https://the-full-stack.com' })

    const parsed = JSON.parse(out)
    const first = parsed.skills[0]
    expect(first.name).toBe(TOOLS[0]?.definition.name)
    expect(first.type).toBe('mcp-tool')
    expect(first.description).toBe(TOOLS[0]?.definition.description)
    expect(first.url).toBe('https://the-full-stack.com/mcp')
  })

  it('Given siteUrl con trailing slash When build Then strippa la slash en la url', () => {
    const out = buildAgentSkills({ siteUrl: 'https://x.com/' })

    const parsed = JSON.parse(out)
    expect(parsed.skills[0].url).toBe('https://x.com/mcp')
  })

  it('Given se invoca When inspecciono Then termina con newline', () => {
    const out = buildAgentSkills({ siteUrl: 'https://x.com' })

    expect(out.endsWith('\n')).toBe(true)
  })

  it('Given se invoca When inspecciono Then es JSON pretty-printed (indent 2)', () => {
    const out = buildAgentSkills({ siteUrl: 'https://x.com' })

    expect(out).toContain('  "skills"')
  })
})
