/**
 * @description Tests para handleToolsCall. Cubre error paths Y happy/error
 *   paths del ciclo execute via vi.mock del registro de tools (asi
 *   Fase 2A no depende de tools reales).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ERROR_CODES } from '../../src/lib/errors'
import { handleToolsCall } from '../../src/lib/handle-tools-call'
import type {
  JsonRpcResponseError,
  JsonRpcResponseSuccess,
  ToolModule,
} from '../../src/lib/types'

const { mockTool, mockThrowingTool } = vi.hoisted(() => {
  return {
    mockTool: {
      definition: {
        name: 'mock_ok',
        description: 'returns ok',
        inputSchema: { type: 'object', properties: {} },
      },
      execute: vi.fn(async () => ({
        content: [{ type: 'text', text: 'OK' }],
      })),
    } as ToolModule,
    mockThrowingTool: {
      definition: {
        name: 'mock_throw',
        description: 'throws',
        inputSchema: { type: 'object', properties: {} },
      },
      execute: vi.fn(async () => {
        throw new Error('boom')
      }),
    } as ToolModule,
  }
})

vi.mock('../../src/lib/tools', () => ({
  TOOLS: [mockTool, mockThrowingTool],
  getToolByName: (name: string): ToolModule | null => {
    if (name === 'mock_ok') return mockTool
    if (name === 'mock_throw') return mockThrowingTool
    return null
  },
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('handleToolsCall - error paths', () => {
  it('Given params=null When invoked Then INVALID_PARAMS', async () => {
    const out = (await handleToolsCall(1, null)) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.INVALID_PARAMS)
    expect(out.error.message).toBe('params must be object')
  })

  it('Given params no objeto When invoked Then INVALID_PARAMS', async () => {
    const out = (await handleToolsCall(1, 'x')) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.INVALID_PARAMS)
  })

  it('Given params sin name When invoked Then INVALID_PARAMS', async () => {
    const out = (await handleToolsCall(1, {})) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.INVALID_PARAMS)
    expect(out.error.message).toBe('missing or empty name')
  })

  it('Given params con name vacio When invoked Then INVALID_PARAMS', async () => {
    const out = (await handleToolsCall(1, {
      name: '',
    })) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.INVALID_PARAMS)
  })

  it('Given params con name no string When invoked Then INVALID_PARAMS', async () => {
    const out = (await handleToolsCall(1, {
      name: 42,
    })) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.INVALID_PARAMS)
  })

  it('Given tool no registrado When invoked Then TOOL_NOT_FOUND', async () => {
    const out = (await handleToolsCall(1, {
      name: 'tool_inexistente',
    })) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.TOOL_NOT_FOUND)
    expect(out.error.message).toBe('tool not found: tool_inexistente')
  })
})

describe('handleToolsCall - happy paths via mock tool registry', () => {
  it('Given tool ok + args object When invoked Then success con content del tool', async () => {
    const out = (await handleToolsCall(1, {
      name: 'mock_ok',
      arguments: { x: 1 },
    })) as JsonRpcResponseSuccess

    expect(out.id).toBe(1)
    expect(out.result).toEqual({ content: [{ type: 'text', text: 'OK' }] })
    expect(mockTool.execute).toHaveBeenCalledWith({ x: 1 })
  })

  it('Given tool ok sin arguments When invoked Then execute recibe objeto vacio', async () => {
    await handleToolsCall(1, { name: 'mock_ok' })

    expect(mockTool.execute).toHaveBeenCalledWith({})
  })

  it('Given arguments no objeto When invoked Then execute recibe objeto vacio', async () => {
    await handleToolsCall(1, { name: 'mock_ok', arguments: 'not-object' })

    expect(mockTool.execute).toHaveBeenCalledWith({})
  })

  it('Given tool throws Error When invoked Then TOOL_EXECUTION_ERROR con message', async () => {
    const out = (await handleToolsCall(1, {
      name: 'mock_throw',
    })) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.TOOL_EXECUTION_ERROR)
    expect(out.error.message).toBe('boom')
  })
})
