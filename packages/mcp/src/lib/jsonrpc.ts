/**
 * @module jsonrpc
 * @description Parse + encode helpers para JSON-RPC 2.0. Pequenisimo
 *   wrapper: la spec es trivial pero centralizamos aqui para no acoplar
 *   handlers al shape exacto.
 */
import type { JsonRpcId, JsonRpcRequest, JsonRpcResponseSuccess } from './types'

/**
 * @function parseRequest
 * @description Parsea un body JSON-RPC. Retorna null si NO es JSON valido,
 *   NO tiene jsonrpc: '2.0', o NO tiene method string. Validacion minima
 *   conforme a la spec (params es opcional, id puede ser null para
 *   notifications — aunque MCP siempre pide id).
 */
export function parseRequest(raw: string): JsonRpcRequest | null {
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return null
  }
  if (typeof parsed !== 'object' || parsed === null) return null
  const obj = parsed as Record<string, unknown>
  if (obj.jsonrpc !== '2.0') return null
  if (typeof obj.method !== 'string') return null
  return {
    jsonrpc: '2.0',
    id: (obj.id as JsonRpcId) ?? null,
    method: obj.method,
    params: obj.params,
  }
}

/**
 * @function makeSuccess
 * @description Construye la envelope de respuesta exitosa JSON-RPC 2.0.
 */
export function makeSuccess(
  id: JsonRpcId,
  result: unknown,
): JsonRpcResponseSuccess {
  return { jsonrpc: '2.0', id, result }
}
