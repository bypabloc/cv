/**
 * @module rooms/past/index (engine)
 * @description Dispatcher de los pasados por sala + el shell comun
 *   `buildPast`: resuelve el builder del set segun `def.id`
 *   (rooms/past/<id>.ts), monta la grieta de salida pegada al muro
 *   trasero y arma el RoomBuild (colliders + updates + dispose). Las
 *   salas de Etapa 2 sin pasado construido aun devuelven un set vacio
 *   (su grieta no existe hasta que la sesion de esa sala lo cree). El
 *   shell sepia lo monta world; el look lo remata el overlay del HUD.
 */
import { Group } from 'three'
import type { RoomId } from '../../../lib/rooms'
import type { Interactable } from '../../state'
import { disposeDeep, outlineGroup } from '../../toon'
import type { PastCtx, RoomBuild } from '../../world'
import { exitPortal } from '../props'
import { aulaPast } from './aula'
import { cofasaPast } from './cofasa'
import { corpoelecPast } from './corpoelec'
import { dibalPast } from './dibal'
import { goodmealPast } from './goodmeal'
import { ipasmePast } from './ipasme'
import type { PastSet, PastSetBuilder } from './shared'

/** Builders por sala; sin entrada = pasado aun no construido (Etapa 2). */
const PAST_BUILDERS: Partial<Record<RoomId, PastSetBuilder>> = {
  aula: aulaPast,
  cofasa: cofasaPast,
  corpoelec: corpoelecPast,
  dibal: dibalPast,
  goodmeal: goodmealPast,
  ipasme: ipasmePast,
}

function buildSet(ctx: PastCtx): PastSet {
  const builder = PAST_BUILDERS[ctx.def.id]
  if (!builder) {
    return {
      group: new Group(),
      colliders: [],
      npcs: [],
      interactables: [],
      updates: [],
    }
  }
  const { x, z, depth } = ctx.pastRoom
  return builder(x, z, depth, ctx.state.locale, ctx.actions)
}

export default function buildPast(ctx: PastCtx): RoomBuild {
  const { pastRoom, state, actions, returnTo } = ctx
  const group = new Group()
  const updates: ((t: number, dt: number) => void)[] = []

  // (el año lo dice el letrero del portal + el caption del HUD)
  const set = buildSet(ctx)
  group.add(set.group)
  const interactables: Interactable[] = [...set.interactables]
  updates.push(...set.updates)
  for (const npc of set.npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }

  // grieta de salida PEGADA al muro trasero, mirando a la sala
  const exit = exitPortal({
    roomIndex: pastRoom.index,
    position: [pastRoom.x, 0, pastRoom.z + pastRoom.depth / 2 - 0.08],
    rotationY: Math.PI,
    locale: state.locale,
    onExit: () => actions.exitPast(returnTo),
  })
  group.add(exit.group)
  if (exit.interactable) {
    interactables.push(exit.interactable)
  }
  if (exit.update) {
    updates.push(exit.update)
  }

  outlineGroup(group, 1.03)

  return {
    group,
    interactables,
    colliders: () => [
      ...set.colliders,
      ...set.npcs.map((npc) => npc.collider()),
    ],
    update: (t, dt) => {
      for (const fn of updates) {
        fn(t, dt)
      }
    },
    dispose: () => {
      for (const npc of set.npcs) {
        npc.dispose()
      }
      disposeDeep(group)
    },
  }
}
