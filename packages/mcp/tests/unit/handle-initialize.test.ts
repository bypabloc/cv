/**
 * @description Tests para handleInitialize (MCP handshake).
 */
import { describe, expect, it } from 'vitest'

import { handleInitialize } from '../../src/lib/handle-initialize'

describe('handleInitialize', () => {
  it('Given id=1 When invoked Then devuelve envelope JSON-RPC 2.0 con MCP fields', () => {
    const out = handleInitialize(1)

    expect(out).toEqual({
      jsonrpc: '2.0',
      id: 1,
      result: {
        protocolVersion: '2025-11-25',
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: 'portfolio-mcp', version: '0.1.0' },
      },
    })
  })

  it('Given id string When invoked Then preserva id', () => {
    const out = handleInitialize('abc')

    expect(out.id).toBe('abc')
  })

  it('Given id null When invoked Then preserva id null', () => {
    const out = handleInitialize(null)

    expect(out.id).toBe(null)
  })
})
