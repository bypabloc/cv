/**
 * @description Tests para handleRequest — router principal del MCP server.
 *   Recibe ahora un MCPDataProvider inyectado por el caller.
 */
import { describe, expect, it } from 'vitest'

import { ERROR_CODES } from '../../src/lib/errors'
import { handleRequest } from '../../src/lib/handle-request'
import type {
  JsonRpcResponseError,
  JsonRpcResponseSuccess,
} from '../../src/lib/types'
import { makeFakeProvider } from './_fakes'

describe('handleRequest', () => {
  it('Given body invalido (no JSON) When handle Then PARSE_ERROR con id null', async () => {
    const out = (await handleRequest(
      'not json',
      makeFakeProvider(),
    )) as JsonRpcResponseError

    expect(out.id).toBe(null)
    expect(out.error.code).toBe(ERROR_CODES.PARSE_ERROR)
  })

  it('Given method=initialize When handle Then result tiene protocolVersion', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":1,"method":"initialize"}',
      makeFakeProvider(),
    )) as JsonRpcResponseSuccess

    expect(out.id).toBe(1)
    expect((out.result as { protocolVersion: string }).protocolVersion).toBe(
      '2025-11-25',
    )
  })

  it('Given method=tools/list When handle Then result tiene 3 tools', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
      makeFakeProvider(),
    )) as JsonRpcResponseSuccess

    const tools = (out.result as { tools: { name: string }[] }).tools
    expect(tools.map((t) => t.name).sort()).toEqual([
      'get_cv_section',
      'list_projects',
      'search_experience',
    ])
  })

  it('Given method=tools/call name=get_cv_section section=about When handle Then result.content[0] empieza con # About', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_cv_section","arguments":{"section":"about"}}}',
      makeFakeProvider(),
    )) as JsonRpcResponseSuccess

    const text = (out.result as { content: { text: string }[] }).content[0]!
      .text
    expect(text.startsWith('# About\n')).toBe(true)
  })

  it('Given method=tools/call sin params When handle Then INVALID_PARAMS', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":3,"method":"tools/call"}',
      makeFakeProvider(),
    )) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.INVALID_PARAMS)
  })

  it('Given method desconocido When handle Then METHOD_NOT_FOUND', async () => {
    const out = (await handleRequest(
      '{"jsonrpc":"2.0","id":4,"method":"foo/bar"}',
      makeFakeProvider(),
    )) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.METHOD_NOT_FOUND)
    expect(out.error.message).toBe('Method not found: foo/bar')
  })

  it('Given JSON sin jsonrpc=2.0 When handle Then PARSE_ERROR', async () => {
    const out = (await handleRequest(
      '{"id":1,"method":"initialize"}',
      makeFakeProvider(),
    )) as JsonRpcResponseError

    expect(out.error.code).toBe(ERROR_CODES.PARSE_ERROR)
  })
})
