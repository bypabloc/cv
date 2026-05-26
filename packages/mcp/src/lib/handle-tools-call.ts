/**
 * @module handle-tools-call
 * @description Maneja `tools/call` de MCP. Valida params, busca el tool
 *   por nombre, invoca execute, mapea errores a JSON-RPC.
 */
import { ERROR_CODES, makeError } from './errors'
import { makeSuccess } from './jsonrpc'
import { getToolByName } from './tools'
import type { JsonRpcId, JsonRpcResponse } from './types'

interface CallParams {
  name?: unknown
  arguments?: unknown
}

export async function handleToolsCall(
  id: JsonRpcId,
  params: unknown,
): Promise<JsonRpcResponse> {
  if (typeof params !== 'object' || params === null) {
    return makeError(id, ERROR_CODES.INVALID_PARAMS, 'params must be object')
  }
  const p = params as CallParams
  if (typeof p.name !== 'string' || p.name.length === 0) {
    return makeError(id, ERROR_CODES.INVALID_PARAMS, 'missing or empty name')
  }
  const tool = getToolByName(p.name)
  if (tool === null) {
    return makeError(
      id,
      ERROR_CODES.TOOL_NOT_FOUND,
      `tool not found: ${p.name}`,
    )
  }
  const args =
    typeof p.arguments === 'object' && p.arguments !== null
      ? (p.arguments as Record<string, unknown>)
      : {}
  try {
    const result = await tool.execute(args)
    return makeSuccess(id, result)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return makeError(id, ERROR_CODES.TOOL_EXECUTION_ERROR, msg)
  }
}
