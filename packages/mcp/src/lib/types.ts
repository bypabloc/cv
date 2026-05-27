/**
 * @module types
 * @description Tipos JSON-RPC 2.0 + tipos MCP (Model Context Protocol)
 *   minimos para implementar el subset de metodos que el portfolio
 *   expone (initialize, tools/list, tools/call).
 *
 *   Spec MCP: https://modelcontextprotocol.io/specification/2025-11-25
 *   Spec JSON-RPC 2.0: https://www.jsonrpc.org/specification
 */

export type JsonRpcId = number | string | null

export interface JsonRpcRequest {
  jsonrpc: '2.0'
  id: JsonRpcId
  method: string
  params?: unknown
}

export interface JsonRpcResponseSuccess {
  jsonrpc: '2.0'
  id: JsonRpcId
  result: unknown
}

export interface JsonRpcResponseError {
  jsonrpc: '2.0'
  id: JsonRpcId
  error: { code: number; message: string; data?: unknown }
}

export type JsonRpcResponse = JsonRpcResponseSuccess | JsonRpcResponseError

export const PROTOCOL_VERSION = '2025-11-25' as const

export interface Capabilities {
  tools?: { listChanged?: boolean }
  resources?: { listChanged?: boolean }
  prompts?: { listChanged?: boolean }
}

export interface ServerInfo {
  name: string
  version: string
}

export interface ToolInputSchema {
  type: 'object'
  properties: Record<string, unknown>
  required?: readonly string[]
}

export interface ToolDefinition {
  name: string
  description: string
  inputSchema: ToolInputSchema
}

export interface ToolContent {
  type: 'text'
  text: string
}

export interface ToolResult {
  content: ToolContent[]
}

export interface ToolModule {
  definition: ToolDefinition
  execute(args: Record<string, unknown>): Promise<ToolResult>
}
