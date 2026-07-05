/**
 * @module rooms/past/shared (engine)
 * @description Piezas comunes de los pasados por sala: el theme de las
 *   pantallas sepia, el contrato `PastSet` que devuelve cada builder, el
 *   label del panel de historia y el helper de NPCs cargando papeles.
 */
import type { Group } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import type { NpcHandle } from '../../character'
import type { Interactable } from '../../state'
import type { PastCtx } from '../../world'
import { paperStack } from '../props'

export const PAST_SCREEN = {
  screenBg: '#2c2620',
  screenFg: '#b08a6a',
  ink: '#201a10',
} as const

/** Escena del "antes" de una sala: props + colliders + NPCs en accion. */
export interface PastSet {
  group: Group
  colliders: Box2[]
  npcs: NpcHandle[]
  interactables: Interactable[]
  updates: ((t: number, dt: number) => void)[]
}

/** Builder del set de un pasado (uno por sala, en rooms/past/<id>.ts). */
export type PastSetBuilder = (
  x: number,
  z: number,
  depth: number,
  locale: Locale,
  actions: PastCtx['actions'],
) => PastSet

export const PAST_STORY_LABEL = {
  es: 'Leer la historia',
  en: 'Read the story',
} as const

/** Pila de papeles cargada al frente del NPC (oficina pre-digital). */
export function carryPapers(npc: NpcHandle): void {
  npc.group.add(paperStack({ position: [0, 1.02, 0.2], count: 6 }))
}
