/**
 * @module state (engine)
 * @description Estado plano del motor vanilla (sin zustand ni pub/sub):
 *   el motor es dueño del objeto y llama metodos del HUD directamente.
 *   Incluye el registro de interactables por proximidad que controls
 *   consulta cada frame y las salas registran/des-registran al montar.
 */
import type { Zone } from '../lib/layout'
import type { Locale } from '../lib/rooms'

/** Tiers que montan el 3D (static nunca llega al engine). */
export type EngineTier = 'full' | 'reduced'
export type CameraMode = 'third' | 'pov'
export type UiPanel = 'none' | 'ficha' | 'contact' | 'teleport'
export type FichaKind = 'retos' | 'aprendizajes'

export interface Interactable {
  id: string
  x: number
  z: number
  radius: number
  label: Record<Locale, string>
  onActivate: () => void
}

export interface FichaRef {
  roomIndex: number
  kind: FichaKind
}

export interface EngineState {
  readonly tier: EngineTier
  readonly locale: Locale
  zone: Zone
  /** Indice de la sala cuyo "antes" se visita (portal al pasado). */
  past: number | null
  doorsOpen: Set<number>
  cameraMode: CameraMode
  /** Panel de UI abierto (los controles se congelan mientras != 'none'). */
  ui: UiPanel
  ficha: FichaRef | null
  /** Audio ambiente: SIEMPRE arranca apagado (autoplay policy, opt-in). */
  audioOn: boolean
  tourOn: boolean
  interactables: Map<string, Interactable>
  activeId: string | null
}

export function createEngineState(
  tier: EngineTier,
  locale: Locale,
): EngineState {
  return {
    tier,
    locale,
    zone: { kind: 'room', index: 0 },
    past: null,
    doorsOpen: new Set(),
    cameraMode: 'third',
    ui: 'none',
    ficha: null,
    audioOn: false,
    tourOn: false,
    interactables: new Map(),
    activeId: null,
  }
}

export function registerInteractable(
  state: EngineState,
  item: Interactable,
): void {
  state.interactables.set(item.id, item)
}

export function unregisterInteractable(state: EngineState, id: string): void {
  state.interactables.delete(id)
  if (state.activeId === id) {
    state.activeId = null
  }
}

/** Ejecuta el interactable activo (tecla E / boton tactil). */
export function activateCurrent(state: EngineState): boolean {
  if (state.activeId === null) {
    return false
  }
  const item = state.interactables.get(state.activeId)
  if (!item) {
    return false
  }
  item.onActivate()
  return true
}

export function isUiOpen(state: EngineState): boolean {
  return state.ui !== 'none'
}

/**
 * @function nearestInteractableIn
 * @description Version Map del `nearestInteractable` de lib/collision:
 *   id del interactable mas cercano dentro de su radio, o null.
 */
export function nearestInteractableIn(
  items: ReadonlyMap<string, Interactable>,
  x: number,
  z: number,
): string | null {
  let bestId: string | null = null
  let bestDistSq = Number.POSITIVE_INFINITY
  for (const item of items.values()) {
    const dx = item.x - x
    const dz = item.z - z
    const distSq = dx * dx + dz * dz
    if (distSq <= item.radius * item.radius && distSq < bestDistSq) {
      bestDistSq = distSq
      bestId = item.id
    }
  }
  return bestId
}
