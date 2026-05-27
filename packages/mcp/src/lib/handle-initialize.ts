/**
 * @module handle-initialize
 * @description Maneja el handshake MCP `initialize`. Devuelve
 *   protocolVersion + capabilities + serverInfo.
 */
import { makeSuccess } from './jsonrpc'
import {
  type Capabilities,
  type JsonRpcId,
  type JsonRpcResponseSuccess,
  PROTOCOL_VERSION,
  type ServerInfo,
} from './types'

const CAPABILITIES: Capabilities = { tools: { listChanged: false } }
const SERVER_INFO: ServerInfo = { name: 'portfolio-mcp', version: '0.1.0' }

export function handleInitialize(id: JsonRpcId): JsonRpcResponseSuccess {
  return makeSuccess(id, {
    protocolVersion: PROTOCOL_VERSION,
    capabilities: CAPABILITIES,
    serverInfo: SERVER_INFO,
  })
}
