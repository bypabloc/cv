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
  execute(
    args: Record<string, unknown>,
    data: MCPDataProvider,
  ): Promise<ToolResult>
}

/**
 * Snapshot shapes (subset de `@portfolio/content`). Definidos aqui para
 * que el bundle de la Pages Function NO arrastre `@portfolio/content`
 * en runtime (ese paquete usa `import.meta.glob` de Vite, incompatible
 * con Cloudflare Workers).
 */
export interface SnapshotBiLang {
  readonly en: string
}

export interface SnapshotProfile {
  readonly summary: SnapshotBiLang
  readonly location: string
  readonly availability?: SnapshotBiLang
  readonly contacts: {
    readonly email: string
    readonly linkedin: string
    readonly github: string
    readonly website: string
  }
}

export interface SnapshotExperience {
  readonly slug: string
  readonly role: SnapshotBiLang
  readonly company: string
  readonly start: string
  readonly end?: string | null
  readonly summary?: SnapshotBiLang
  readonly achievements: { readonly en: readonly string[] }
  readonly skillsTechnical?: readonly string[]
}

export interface SnapshotProject {
  readonly slug: string
  readonly name: string
  readonly summary: SnapshotBiLang
  readonly stack: readonly string[]
  readonly url?: string | null
}

export interface SnapshotSkillCategory {
  readonly name: SnapshotBiLang
  readonly skills: readonly string[]
}

export interface SnapshotEducation {
  readonly institution: string
  readonly degree?: SnapshotBiLang
  readonly start?: string | null
  readonly end?: string | null
}

export interface CvSnapshot {
  readonly profile: SnapshotProfile
  readonly experiences: readonly SnapshotExperience[]
  readonly projects: readonly SnapshotProject[]
  readonly skills: readonly SnapshotSkillCategory[]
  readonly education: readonly SnapshotEducation[]
}

export interface MCPDataProvider {
  getProfile(): SnapshotProfile
  getExperiences(): readonly SnapshotExperience[]
  getProjects(): readonly SnapshotProject[]
  getSkills(): readonly SnapshotSkillCategory[]
  getEducation(): readonly SnapshotEducation[]
}
