/**
 * @module handle-request
 * @description Router principal. Recibe el body raw del POST /mcp,
 *   parsea JSON-RPC, ruta por method y devuelve la response envelope.
 *
 *   Metodos soportados:
 *   - initialize: handshake MCP
 *   - tools/list: lista de tools
 *   - tools/call: ejecuta un tool por nombre
 *
 *   Cualquier otro method -> error METHOD_NOT_FOUND.
 *   Body malformado -> error PARSE_ERROR.
 */
import { ERROR_CODES, makeError } from './errors'
import { handleInitialize } from './handle-initialize'
import { handleToolsCall } from './handle-tools-call'
import { handleToolsList } from './handle-tools-list'
import { parseRequest } from './jsonrpc'
import type { JsonRpcResponse } from './types'

export async function handleRequest(body: string): Promise<JsonRpcResponse> {
  const req = parseRequest(body)
  if (req === null) {
    return makeError(null, ERROR_CODES.PARSE_ERROR, 'Parse error')
  }

  switch (req.method) {
    case 'initialize':
      return handleInitialize(req.id)
    case 'tools/list':
      return handleToolsList(req.id)
    case 'tools/call':
      return handleToolsCall(req.id, req.params)
    default:
      return makeError(
        req.id,
        ERROR_CODES.METHOD_NOT_FOUND,
        `Method not found: ${req.method}`,
      )
  }
}
