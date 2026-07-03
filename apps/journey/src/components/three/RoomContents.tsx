/**
 * @component RoomContents
 * @description Carga LAZY del contenido de cada sala (chunk por sala, regla
 *   del plan): solo se montan la sala actual y sus adyacentes; la escena
 *   del pasado solo mientras se visita. El `Suspense` queda cubierto por el
 *   pasillo/puerta (el "pasillo de carga").
 */
import { type ComponentType, lazy, Suspense } from 'react'
import type { JourneyLayout, PastRoomLayout, WallBox } from '../../lib/layout'
import type { RoomDef, RoomId } from '../../lib/rooms'
import { useJourneyStore } from '../../lib/store'
import type { RoomSceneProps } from './rooms/shared'
import { ShadowGroup } from './ShadowGroup'

// ComponentType importado de 'react' (nunca el namespace global React.*:
// resolveria al @types/react 19 hoisted del admin -> TS2786 'bigint')
const SCENES: Record<RoomId, ComponentType<RoomSceneProps>> = {
  aula: lazy(() => import('./rooms/AulaScene')),
  corpoelec: lazy(() => import('./rooms/CorpoelecScene')),
  cima: lazy(() => import('./rooms/CimaScene')),
}

const PastScene = lazy(() => import('./rooms/PastScene'))

interface RoomContentsProps {
  rooms: readonly RoomDef[]
  layout: JourneyLayout
  pastRooms: readonly PastRoomLayout[]
  pastWalls: readonly WallBox[]
}

export function RoomContents({
  rooms,
  layout,
  pastRooms,
  pastWalls,
}: RoomContentsProps) {
  const zone = useJourneyStore((s) => s.zone)
  const past = useJourneyStore((s) => s.past)

  // sala actual + adyacentes (el pasillo precarga la siguiente)
  const current = zone.index
  const visible = new Set(
    zone.kind === 'corridor'
      ? [current, current + 1]
      : [current - 1, current, current + 1],
  )

  const pastDef = past !== null ? rooms[past] : null
  const pastRoom = past !== null ? pastRooms[past] : null

  return (
    <group>
      {rooms.map((def) => {
        const room = layout.rooms[def.order]
        if (!room || !visible.has(def.order)) {
          return null
        }
        const Scene = SCENES[def.id]
        return (
          <Suspense key={def.id} fallback={null}>
            <ShadowGroup>
              <Scene room={room} def={def} />
            </ShadowGroup>
          </Suspense>
        )
      })}
      {pastDef && pastRoom && (
        <Suspense fallback={null}>
          <ShadowGroup>
            <PastScene
              def={pastDef}
              pastRoom={pastRoom}
              walls={pastWalls}
              layout={layout}
            />
          </ShadowGroup>
        </Suspense>
      )}
    </group>
  )
}
