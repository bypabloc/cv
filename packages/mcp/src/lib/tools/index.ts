/**
 * @module tools/index
 * @description Registro central de tools MCP. En Fase 2A esta vacio
 *   (handlers tools/list devuelve []); en Fase 2B se llenan con 3 tools.
 */
import type { ToolModule } from '../types'

export const TOOLS: readonly ToolModule[] = []

export function getToolByName(name: string): ToolModule | null {
  return TOOLS.find((t) => t.definition.name === name) ?? null
}
