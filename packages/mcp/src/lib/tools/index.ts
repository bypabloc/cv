/**
 * @module tools/index
 * @description Registro central de tools MCP. Las 3 tools del portfolio
 *   exponen el CV via JSON-RPC tools/call.
 */

import type { ToolModule } from '../types'
import * as getCvSection from './get-cv-section'
import * as listProjects from './list-projects'
import * as searchExperience from './search-experience'

export const TOOLS: readonly ToolModule[] = [
  getCvSection,
  listProjects,
  searchExperience,
]

export function getToolByName(name: string): ToolModule | null {
  return TOOLS.find((t) => t.definition.name === name) ?? null
}
