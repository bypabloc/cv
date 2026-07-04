/**
 * @module rooms/past (engine)
 * @description Factory de las mini-salas del pasado (portal). Stub del
 *   contrato PastCtx (el clutter sepia se porta en el commit de salas).
 */
import { Group } from 'three'
import { disposeDeep } from '../toon'
import type { PastCtx, RoomBuild } from '../world'

export default function buildPast(_ctx: PastCtx): RoomBuild {
  const group = new Group()
  return {
    group,
    interactables: [],
    dispose: () => disposeDeep(group),
  }
}
