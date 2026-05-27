/**
 * @description Tests para makeError + ERROR_CODES.
 */
import { describe, expect, it } from 'vitest'

import { ERROR_CODES, makeError } from '../../src/lib/errors'

describe('ERROR_CODES', () => {
  it('Given se inspecciona When leo codes Then estandar JSON-RPC + MCP custom', () => {
    expect(ERROR_CODES.PARSE_ERROR).toBe(-32700)
    expect(ERROR_CODES.INVALID_REQUEST).toBe(-32600)
    expect(ERROR_CODES.METHOD_NOT_FOUND).toBe(-32601)
    expect(ERROR_CODES.INVALID_PARAMS).toBe(-32602)
    expect(ERROR_CODES.INTERNAL_ERROR).toBe(-32603)
    expect(ERROR_CODES.TOOL_NOT_FOUND).toBe(-32001)
    expect(ERROR_CODES.TOOL_EXECUTION_ERROR).toBe(-32002)
  })
})

describe('makeError', () => {
  it('Given id+code+message When build Then envelope JSON-RPC 2.0', () => {
    const out = makeError(1, ERROR_CODES.METHOD_NOT_FOUND, 'Method not found')

    expect(out).toEqual({
      jsonrpc: '2.0',
      id: 1,
      error: { code: -32601, message: 'Method not found' },
    })
  })

  it('Given data When build Then incluye data en el envelope', () => {
    const out = makeError(1, -32603, 'Internal', { trace: 'x' })

    expect(out.error.data).toEqual({ trace: 'x' })
  })

  it('Given sin data When build Then no incluye campo data', () => {
    const out = makeError(1, -32603, 'Internal')

    expect('data' in out.error).toBe(false)
  })

  it('Given id null When build Then preserva id null', () => {
    const out = makeError(null, -32700, 'Parse')

    expect(out.id).toBe(null)
  })
})
