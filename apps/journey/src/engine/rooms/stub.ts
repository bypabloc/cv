/**
 * @module rooms/stub (engine)
 * @description Placeholder "en construccion" para las salas de Etapa 2 del
 *   plan journey-salas-estandar que aun no se construyen: sobre el shell
 *   del theme (paredes blancas + acento) monta un cartel con el titulo de
 *   la etapa + una barrera de obra con el acento (~4 draw calls). Cada
 *   sesion de Etapa 2 reemplaza el stub por la escena real.
 */
import { Group } from 'three'
import type { Box2 } from '../../lib/collision'
import { disposeDeep, label, mergedBoxes, outlineGroup, toonMat } from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import { footprint } from './props'

const SIGN = {
  es: 'SALA EN CONSTRUCCION',
  en: 'ROOM UNDER CONSTRUCTION',
} as const

/** Sala placeholder: cartel del titulo + barrera de obra. */
export function underConstruction(ctx: RoomCtx): RoomBuild {
  const { def, room, theme, state } = ctx
  const group = new Group()
  const texts = def.texts[state.locale]

  // cartel flotante: titulo de la etapa (acento) + aviso (tinta), de cara
  // al jugador que entra caminando hacia +Z
  const title = label(texts.title, { size: 0.4, color: theme.accent })
  title.position.set(room.x, 2.4, room.z + 1.6)
  title.rotation.y = Math.PI
  const sign = label(SIGN[state.locale], { size: 0.22, color: theme.ink })
  sign.position.set(room.x, 1.85, room.z + 1.6)
  sign.rotation.y = Math.PI

  // barrera de obra: 2 postes + 2 tablones con el acento del rubro
  const barrier = mergedBoxes(
    [
      { w: 0.09, h: 1.05, d: 0.09, x: -1.2, y: 0.52, z: 0 },
      { w: 0.09, h: 1.05, d: 0.09, x: 1.2, y: 0.52, z: 0 },
      { w: 2.6, h: 0.14, d: 0.05, x: 0, y: 0.86, z: 0 },
      { w: 2.6, h: 0.14, d: 0.05, x: 0, y: 0.42, z: 0 },
    ],
    toonMat(theme.accent),
  )
  barrier.position.set(room.x, 0, room.z + 0.4)
  group.add(title, sign, barrier)
  outlineGroup(group, 1.03)

  const colliders: Box2[] = [footprint(room.x, room.z + 0.4, 2.8, 0.3)]
  return {
    group,
    interactables: [],
    colliders: () => colliders,
    dispose: () => disposeDeep(group),
  }
}
