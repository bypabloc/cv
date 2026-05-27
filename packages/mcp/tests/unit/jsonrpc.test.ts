/**
 * @description Tests para parseRequest + makeSuccess (JSON-RPC 2.0).
 */
import { describe, expect, it } from 'vitest'

import { makeSuccess, parseRequest } from '../../src/lib/jsonrpc'

describe('parseRequest', () => {
  it('Given valid JSON-RPC 2.0 con method+id When parse Then devuelve objeto parseado', () => {
    const out = parseRequest('{"jsonrpc":"2.0","id":1,"method":"initialize"}')

    expect(out).toEqual({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: undefined,
    })
  })

  it('Given JSON-RPC con params When parse Then preserva params', () => {
    const out = parseRequest(
      '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"x"}}',
    )

    expect(out).toEqual({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: { name: 'x' },
    })
  })

  it('Given JSON-RPC con id string When parse Then preserva id', () => {
    const out = parseRequest(
      '{"jsonrpc":"2.0","id":"abc","method":"initialize"}',
    )

    expect(out?.id).toBe('abc')
  })

  it('Given JSON-RPC sin id When parse Then id es null', () => {
    const out = parseRequest('{"jsonrpc":"2.0","method":"initialize"}')

    expect(out?.id).toBe(null)
  })

  it('Given JSON invalido When parse Then devuelve null', () => {
    expect(parseRequest('not json')).toBe(null)
  })

  it('Given JSON valido pero no objeto When parse Then devuelve null', () => {
    expect(parseRequest('"string"')).toBe(null)
    expect(parseRequest('42')).toBe(null)
    expect(parseRequest('null')).toBe(null)
  })

  it('Given missing jsonrpc=2.0 When parse Then devuelve null', () => {
    expect(parseRequest('{"id":1,"method":"x"}')).toBe(null)
    expect(parseRequest('{"jsonrpc":"1.0","id":1,"method":"x"}')).toBe(null)
  })

  it('Given missing method When parse Then devuelve null', () => {
    expect(parseRequest('{"jsonrpc":"2.0","id":1}')).toBe(null)
  })

  it('Given method no string When parse Then devuelve null', () => {
    expect(parseRequest('{"jsonrpc":"2.0","id":1,"method":42}')).toBe(null)
  })
})

describe('makeSuccess', () => {
  it('Given id+result When invoked Then devuelve envelope JSON-RPC 2.0', () => {
    const out = makeSuccess(1, { ok: true })

    expect(out).toEqual({ jsonrpc: '2.0', id: 1, result: { ok: true } })
  })

  it('Given id null+result When invoked Then preserva id null', () => {
    const out = makeSuccess(null, 'x')

    expect(out).toEqual({ jsonrpc: '2.0', id: null, result: 'x' })
  })
})
