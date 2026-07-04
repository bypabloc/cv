/**
 * @module rooms/aula (engine)
 * @description Factory de la sala 0 — Aula/Universidad. Stub del contrato
 *   RoomCtx (el contenido narrativo se porta en el commit de salas).
 */
import { Group } from 'three'
import { disposeDeep } from '../toon'
import type { RoomBuild, RoomCtx } from '../world'

export default function buildAula(_ctx: RoomCtx): RoomBuild {
  const group = new Group()
  return {
    group,
    interactables: [],
    dispose: () => disposeDeep(group),
  }
}
