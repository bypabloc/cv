/**
 * @module rooms/corpoelec (engine)
 * @description Factory de la sala 1 — CORPOELEC. Stub del contrato RoomCtx
 *   (el contenido narrativo se porta en el commit de salas).
 */
import { Group } from 'three'
import { disposeDeep } from '../toon'
import type { RoomBuild, RoomCtx } from '../world'

export default function buildCorpoelec(_ctx: RoomCtx): RoomBuild {
  const group = new Group()
  return {
    group,
    interactables: [],
    dispose: () => disposeDeep(group),
  }
}
