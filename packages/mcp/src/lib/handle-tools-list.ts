/**
 * @module handle-tools-list
 * @description Maneja `tools/list` de MCP. Devuelve la lista de
 *   definitions (sin executar nada).
 */
import { makeSuccess } from './jsonrpc'
import { TOOLS } from './tools'
import type { JsonRpcId, JsonRpcResponseSuccess } from './types'

export function handleToolsList(id: JsonRpcId): JsonRpcResponseSuccess {
  return makeSuccess(id, { tools: TOOLS.map((t) => t.definition) })
}
