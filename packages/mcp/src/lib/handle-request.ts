/**
 * @module handle-request
 * @description Router principal. Recibe el body raw del POST /mcp,
 *   parsea JSON-RPC, ruta por method y devuelve la response envelope.
 *
 *   El caller (la Pages Function de cada niche) inyecta un
 *   `MCPDataProvider` con los datos del CV pre-buildeados (snapshot
 *   JSON). El bundle de Workers NO puede importar `@portfolio/content`
 *   en runtime (usa `import.meta.glob`), por eso la inyeccion.
 *
 *   Metodos soportados:
 *   - initialize: handshake MCP
 *   - tools/list: lista de tools (no requiere data)
 *   - tools/call: ejecuta un tool por nombre (recibe data)
 *
 *   Cualquier otro method -> error METHOD_NOT_FOUND.
 *   Body malformado -> error PARSE_ERROR.
 */
import { ERROR_CODES, makeError } from './errors'
import { handleInitialize } from './handle-initialize'
import { handleToolsCall } from './handle-tools-call'
import { handleToolsList } from './handle-tools-list'
import { parseRequest } from './jsonrpc'
import type { JsonRpcResponse, MCPDataProvider } from './types'

export async function handleRequest(
  body: string,
  data: MCPDataProvider,
): Promise<JsonRpcResponse> {
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
      return handleToolsCall(req.id, req.params, data)
    default:
      return makeError(
        req.id,
        ERROR_CODES.METHOD_NOT_FOUND,
        `Method not found: ${req.method}`,
      )
  }
}
