/**
 * @module @portfolio/mcp
 * @description Servidor MCP (Model Context Protocol) para el portfolio.
 *   Implementa JSON-RPC 2.0 sobre HTTP. 3 metodos: initialize, tools/list,
 *   tools/call. 3 tools (Fase 2B): get_cv_section, list_projects,
 *   search_experience.
 *
 *   Consumido por las 6 Cloudflare Pages Functions en
 *   `apps/<niche>/functions/mcp.ts` (wrapper thin que llama handleRequest).
 */
export { handleRequest } from './lib/handle-request'
export { createSnapshotProvider } from './lib/snapshot-provider'
export { getToolByName, TOOLS } from './lib/tools'
export type {
  Capabilities,
  CvSnapshot,
  JsonRpcId,
  JsonRpcRequest,
  JsonRpcResponse,
  JsonRpcResponseError,
  JsonRpcResponseSuccess,
  MCPDataProvider,
  ServerInfo,
  SnapshotBiLang,
  SnapshotEducation,
  SnapshotExperience,
  SnapshotProfile,
  SnapshotProject,
  SnapshotSkillCategory,
  ToolContent,
  ToolDefinition,
  ToolInputSchema,
  ToolModule,
  ToolResult,
} from './lib/types'
export { PROTOCOL_VERSION } from './lib/types'
