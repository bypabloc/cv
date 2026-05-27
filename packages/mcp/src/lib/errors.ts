/**
 * @module errors
 * @description Codigos de error JSON-RPC 2.0 estandar + extensiones
 *   especificas de MCP usadas por handleToolsCall.
 */
import type { JsonRpcId, JsonRpcResponseError } from './types'

export const ERROR_CODES = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
  // MCP-specific (reservados en el rango -32099..-32000 por la spec
  // JSON-RPC para errores del servidor)
  TOOL_NOT_FOUND: -32001,
  TOOL_EXECUTION_ERROR: -32002,
} as const

export function makeError(
  id: JsonRpcId,
  code: number,
  message: string,
  data?: unknown,
): JsonRpcResponseError {
  const error: JsonRpcResponseError['error'] = { code, message }
  if (data !== undefined) {
    error.data = data
  }
  return { jsonrpc: '2.0', id, error }
}
