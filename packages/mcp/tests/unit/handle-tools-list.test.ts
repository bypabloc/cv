/**
 * @description Tests para handleToolsList — devuelve la lista de tools
 *   registrados. Fase 2B: 3 tools (get_cv_section, list_projects,
 *   search_experience).
 */
import { describe, expect, it } from 'vitest'

import { handleToolsList } from '../../src/lib/handle-tools-list'
import { TOOLS } from '../../src/lib/tools'

describe('handleToolsList', () => {
  it('Given id=1 When invoked Then devuelve envelope JSON-RPC 2.0 con tools array', () => {
    const out = handleToolsList(1)

    expect(out).toEqual({
      jsonrpc: '2.0',
      id: 1,
      result: { tools: TOOLS.map((t) => t.definition) },
    })
  })

  it('Given se inspecciona el result When leo tools.length Then matchea TOOLS.length', () => {
    const out = handleToolsList(1)
    const tools = (out.result as { tools: unknown[] }).tools

    expect(tools.length).toBe(TOOLS.length)
  })

  it('Given Fase 2B completa When leo nombres Then son los 3 tools esperados en orden estable', () => {
    const out = handleToolsList(1)
    const tools = (out.result as { tools: Array<{ name: string }> }).tools

    expect(tools.map((t) => t.name)).toEqual([
      'get_cv_section',
      'list_projects',
      'search_experience',
    ])
  })
})
