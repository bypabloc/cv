/**
 * @module state (engine)
 * @description Estado plano del motor vanilla (sin store lib ni pub/sub):
 *   el motor es dueño del objeto y llama metodos del HUD directamente.
 *   Incluye el registro de interactables por proximidad que controls
 *   consulta cada frame y las salas registran/des-registran al montar.
 */
import type { Box2 } from '../lib/collision'
import type { Zone } from '../lib/layout'
import type { Locale } from '../lib/rooms'

/** Tiers que montan el 3D (static nunca llega al engine). */
export type EngineTier = 'full' | 'reduced'
export type CameraMode = 'third' | 'pov'
export type UiPanel =
  | 'none'
  | 'ficha'
  | 'contact'
  | 'teleport'
  | 'dialog'
  | 'showcase'
export type FichaKind = 'retos' | 'aprendizajes'

/** Vista de la demo activa de un `softwareShowcase` (panel DOM del HUD). */
export interface ShowcaseView {
  /** Titulo de la demo (resuelto por locale). */
  title: string
  /** Color de branding del sistema real (barra del panel). */
  brand: string
  /** Markup del mockup operable (HTML definido en codigo, no user input). */
  html: string
  /** Posicion de la demo en el ciclo (ej. "1/3"). */
  position: string
}

/** Referencia viva al showcase abierto: E / boton ciclan a la siguiente. */
export interface ShowcaseRef {
  view(): ShowcaseView
  /** Cicla a la siguiente demo (tambien actualiza el monitor 3D). */
  next(): ShowcaseView
}

/** Burbuja manga de "habla suelta": 1 linea al azar sobre el NPC activo. */
export interface InteractableBubble {
  lines: readonly Record<Locale, string>[]
  /** Punto de anclaje mundial (la cabeza del NPC), evaluado por frame. */
  anchor(): { x: number; y: number; z: number }
}

export interface Interactable {
  id: string
  x: number
  z: number
  radius: number
  label: Record<Locale, string>
  /** Recibe la posicion del jugador (los NPCs se giran a mirarlo). */
  onActivate: (player?: { x: number; z: number }) => void
  bubble?: InteractableBubble
}

export interface FichaRef {
  roomIndex: number
  kind: FichaKind
}

/** Silla objetivo al sentarse: posicion exacta + orientacion del jugador. */
export interface SeatTarget {
  x: number
  z: number
  rotationY: number
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
  /** Audio ON por defecto (arranca recien tras el PRIMER gesto — autoplay
   *  policy); el toggle del HUD silencia TODO (ambiente + SFX). */
  audioOn: boolean
  tourOn: boolean
  /** Silla donde esta sentado el jugador, o null si esta de pie. */
  playerSeat: SeatTarget | null
  interactables: Map<string, Interactable>
  activeId: string | null
  /**
   * Colliders del CONTENIDO por fuente (sala montada / pasado): cada
   * fuente es una funcion evaluada por frame (cubre props estaticos y
   * NPCs en movimiento). Los registra/borra el world al montar/desmontar.
   */
  obstacleSources: Map<string, () => readonly Box2[]>
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
    audioOn: true,
    tourOn: false,
    playerSeat: null,
    interactables: new Map(),
    activeId: null,
    obstacleSources: new Map(),
  }
}

/** Aplana los colliders de contenido activos (props + NPCs) del frame. */
export function collectObstacles(state: EngineState): Box2[] {
  const out: Box2[] = []
  for (const source of state.obstacleSources.values()) {
    out.push(...source())
  }
  return out
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
export function activateCurrent(
  state: EngineState,
  player?: { x: number; z: number },
): boolean {
  if (state.activeId === null) {
    return false
  }
  const item = state.interactables.get(state.activeId)
  if (!item) {
    return false
  }
  item.onActivate(player)
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
