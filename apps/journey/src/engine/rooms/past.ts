/**
 * @module rooms/past (engine)
 * @description Mini-sala sepia del "antes" (portal al pasado): clutter
 *   especifico por sala (papeles, archivador, planillas), cartel
 *   ANTES · {año} y portal de salida. El shell (muros/piso/techo/luz) lo
 *   monta world; el look sepia lo remata el overlay CSS del HUD.
 */
import { Group } from 'three'
import type { RoomDef } from '../../lib/rooms'
import type { Interactable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  outlineGroup,
  screenPanel,
  toonMat,
} from '../toon'
import type { PastCtx, RoomBuild } from '../world'
import { desk, exitPortal, paperStack } from './props'

const PAST_SCREEN = { screenBg: '#2c2620', screenFg: '#b08a6a', ink: '#201a10' }

/** Clutter del "antes" segun la sala. */
function pastClutter(def: RoomDef, x: number, z: number, depth: number): Group {
  const group = new Group()
  if (def.id === 'aula') {
    group.add(
      desk({
        position: [x - 1.2, 0, z - 0.6],
        rotationY: 0.3,
        color: '#4a3b2a',
      }),
      desk({
        position: [x + 1.1, 0, z + 0.4],
        rotationY: -0.5,
        color: '#4a3b2a',
      }),
      paperStack({ position: [x - 1.2, 0.76, z - 0.6], count: 10 }),
      paperStack({ position: [x + 1.1, 0.76, z + 0.4], count: 14 }),
      paperStack({ position: [x + 0.2, 0, z - 1.4], count: 18 }),
    )
    const panel = screenPanel({
      title: 'X X X',
      lines: ['plan tachado', 'meses sin avance', 'dos equipos frustrados'],
      theme: PAST_SCREEN,
      width: 1.8,
      height: 1.1,
    })
    panel.position.set(x, 1.6, z - depth / 2 + 0.12)
    group.add(panel)
    return group
  }
  if (def.id === 'corpoelec') {
    for (const dx of [-1.4, 0, 1.4]) {
      group.add(
        desk({ position: [x + dx, 0, z - 0.4], color: '#4c4740' }),
        paperStack({ position: [x + dx, 0.76, z - 0.4], count: 12 }),
      )
    }
    const cabinet = boxMesh(0.6, 1.8, 0.5, toonMat('#5a5750'))
    cabinet.position.set(x + 2.5, 0.9, z + 1.6)
    group.add(cabinet)
    const panel = screenPanel({
      title: 'planillas duplicadas',
      lines: [
        'sede A: copia 1',
        'sede B: copia 2 (distinta)',
        'sede C: perdida',
      ],
      theme: PAST_SCREEN,
      width: 1.8,
      height: 1.1,
    })
    panel.position.set(x, 1.6, z - depth / 2 + 0.12)
    group.add(panel)
    return group
  }
  group.add(
    desk({ position: [x, 0, z - 0.4], width: 1.6, color: '#3c3a44' }),
    paperStack({ position: [x - 0.4, 0.76, z - 0.4], count: 16 }),
    paperStack({ position: [x + 0.4, 0.76, z - 0.4], count: 9 }),
  )
  const panel = screenPanel({
    title: 'procesos manuales',
    lines: [
      'admin de campanas: horas',
      'servicios sin orquestar',
      'un solo pais, silos',
    ],
    theme: PAST_SCREEN,
    width: 2,
    height: 1.1,
  })
  panel.position.set(x, 1.6, z - depth / 2 + 0.12)
  group.add(panel)
  return group
}

export default function buildPast(ctx: PastCtx): RoomBuild {
  const { def, pastRoom, state, actions, returnTo } = ctx
  const group = new Group()
  const interactables: Interactable[] = []

  // cartel ANTES · {año} cerca del techo, mirando a la entrada
  const sign = label(
    state.locale === 'es' ? `ANTES · ${def.year}` : `BEFORE · ${def.year}`,
    { size: 0.3, color: '#c8a878' },
  )
  sign.position.set(
    pastRoom.x,
    pastRoom.height - 0.5,
    pastRoom.z + pastRoom.depth / 2 - 0.3,
  )
  sign.rotation.y = Math.PI
  group.add(sign)

  group.add(pastClutter(def, pastRoom.x, pastRoom.z, pastRoom.depth))

  const exit = exitPortal({
    roomIndex: pastRoom.index,
    position: [pastRoom.x, 0, pastRoom.z + pastRoom.depth / 2 - 0.6],
    onExit: () => actions.exitPast(returnTo),
  })
  group.add(exit.group)
  if (exit.interactable) {
    interactables.push(exit.interactable)
  }

  outlineGroup(group, 1.03)

  return {
    group,
    interactables,
    dispose: () => disposeDeep(group),
  }
}
