/**
 * @description Tests para handleRequest — router principal del MCP server.
 */
import { describe, expect, it } from 'vitest'

import { ERROR_CODES } from '../../src/lib/errors'
import { handleRequest } from '../../src/lib/handle-request'
import type {
  JsonRpcResponseError,
  JsonRpcResponseSuccess,
} from '../../src/lib/types'

describe('handleRequest', () => {
  it('Given body invalido (no JSON) When handle Then PARSE_ERROR con id null', async () => {
    const out = (await handleRequest('not json')) as JsonRpcResponseError

    expect(out.id).toBe(null)
    expect(out.error.code).toBe(ERROR_CODES.PARSE_ERROR)
  })

  it('Given method=initialize When handle Then result tiene protocolVersion', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":1,"method":"initialize"}',
    )) as JsonRpcResponseSuccess

    expect(out.id).toBe(1)
    expect((out.result as { protocolVersion: string }).protocolVersion).toBe(
      '2025-11-25',
    )
  })

  it('Given method=tools/list When handle Then result tiene tools array', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
    )) as JsonRpcResponseSuccess

    expect(Array.isArray((out.result as { tools: unknown[] }).tools)).toBe(true)
  })

  it('Given method=tools/call sin params When handle Then INVALID_PARAMS', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":3,"method":"tools/call"}',
    )) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.INVALID_PARAMS)
  })

  it('Given method desconocido When handle Then METHOD_NOT_FOUND', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":4,"method":"foo/bar"}',
    )) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.METHOD_NOT_FOUND)
    expect(out.error.message).toBe('Method not found: foo/bar')
  })

  it('Given JSON sin jsonrpc=2.0 When handle Then PARSE_ERROR', async () => {
    const out = (await handleRequest(
      '{"id":1,"method":"initialize"}',
    )) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.PARSE_ERROR)
  })
})
