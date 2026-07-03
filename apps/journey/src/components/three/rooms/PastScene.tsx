/**
 * @component PastScene
 * @description La mini-escena "antes" de una sala (portal al pasado):
 *   sala espejo desplazada en X, con el caos manual que la solucion
 *   elimino. El look sepia/glitch lo aplica el overlay CSS de JourneyApp
 *   (filter sobre el canvas), no un shader — barato y suficiente.
 */
import { Text } from '@react-three/drei'
import { useMemo } from 'react'
import type {
  JourneyLayout,
  PastRoomLayout,
  WallBox,
} from '../../../lib/layout'
import type { RoomDef } from '../../../lib/rooms'
import { useJourneyStore } from '../../../lib/store'
import { plasterTexture, tileTexture } from '../textures'
import { Desk, ExitPortal, PaperStack, ScreenPanel } from './shared'

interface PastSceneProps {
  def: RoomDef
  pastRoom: PastRoomLayout
  walls: readonly WallBox[]
  layout: JourneyLayout
}

/** Clutter del "antes" segun la sala. */
function PastClutter({
  def,
  pastRoom,
}: {
  def: RoomDef
  pastRoom: PastRoomLayout
}) {
  const { x, z } = pastRoom
  if (def.id === 'aula') {
    return (
      <group>
        <Desk
          position={[x - 1.2, 0, z - 0.6]}
          rotationY={0.3}
          color="#4a3b2a"
        />
        <Desk
          position={[x + 1.1, 0, z + 0.4]}
          rotationY={-0.5}
          color="#4a3b2a"
        />
        <PaperStack position={[x - 1.2, 0.76, z - 0.6]} count={10} />
        <PaperStack position={[x + 1.1, 0.76, z + 0.4]} count={14} />
        <PaperStack position={[x + 0.2, 0, z - 1.4]} count={18} />
        <ScreenPanel
          position={[x, 1.6, z - pastRoom.depth / 2 + 0.12]}
          width={1.8}
          height={1.1}
          title="X X X"
          lines={['plan tachado', 'meses sin avance', 'dos equipos frustrados']}
          bg="#2c2620"
          fg="#b08a6a"
        />
      </group>
    )
  }
  if (def.id === 'corpoelec') {
    return (
      <group>
        {[-1.4, 0, 1.4].map((dx) => (
          <group key={dx}>
            <Desk position={[x + dx, 0, z - 0.4]} color="#4c4740" />
            <PaperStack position={[x + dx, 0.76, z - 0.4]} count={12} />
          </group>
        ))}
        {/* archivador */}
        <mesh position={[x + pastRoom.width / 2 - 0.5, 0.9, z + 1.6]}>
          <boxGeometry args={[0.6, 1.8, 0.5]} />
          <meshStandardMaterial color="#5a5750" roughness={0.8} />
        </mesh>
        <ScreenPanel
          position={[x, 1.6, z - pastRoom.depth / 2 + 0.12]}
          width={1.8}
          height={1.1}
          title="planillas duplicadas"
          lines={[
            'sede A: copia 1',
            'sede B: copia 2 (distinta)',
            'sede C: perdida',
          ]}
          bg="#2c2620"
          fg="#b08a6a"
        />
      </group>
    )
  }
  return (
    <group>
      <Desk position={[x, 0, z - 0.4]} width={1.6} color="#3c3a44" />
      <PaperStack position={[x - 0.4, 0.76, z - 0.4]} count={16} />
      <PaperStack position={[x + 0.4, 0.76, z - 0.4]} count={9} />
      <ScreenPanel
        position={[x, 1.6, z - pastRoom.depth / 2 + 0.12]}
        width={2}
        height={1.1}
        title="procesos manuales"
        lines={[
          'admin de campanas: horas',
          'servicios sin orquestar',
          'un solo pais, silos',
        ]}
        bg="#2c2620"
        fg="#b08a6a"
      />
    </group>
  )
}

export default function PastScene({
  def,
  pastRoom,
  walls,
  layout,
}: PastSceneProps) {
  const locale = useJourneyStore((s) => s.locale)
  const wallTexture = useMemo(
    () => plasterTexture('#3a352c', '#c8b088', 21, true),
    [],
  )
  const floorTexture = useMemo(
    () => tileTexture('#2d2921', '#221f19', 4, 23),
    [],
  )
  const room = layout.rooms[pastRoom.index]
  const returnTo = useMemo(
    () => ({ x: 0, z: room ? room.z - room.depth / 2 + 1.5 : 2 }),
    [room],
  )
  const myWalls = walls.filter((w) => w.source.index === pastRoom.index)

  return (
    <group>
      {myWalls.map((wall) => (
        <mesh
          key={`past-${wall.minX}:${wall.maxX}:${wall.minZ}:${wall.maxZ}`}
          position={[
            (wall.minX + wall.maxX) / 2,
            wall.height / 2,
            (wall.minZ + wall.maxZ) / 2,
          ]}
        >
          <boxGeometry
            args={[wall.maxX - wall.minX, wall.height, wall.maxZ - wall.minZ]}
          />
          <meshStandardMaterial map={wallTexture} roughness={1} />
        </mesh>
      ))}
      <mesh rotation-x={-Math.PI / 2} position={[pastRoom.x, 0, pastRoom.z]}>
        <planeGeometry args={[pastRoom.width, pastRoom.depth]} />
        <meshStandardMaterial map={floorTexture} roughness={1} />
      </mesh>
      <mesh
        rotation-x={Math.PI / 2}
        position={[pastRoom.x, pastRoom.height, pastRoom.z]}
      >
        <planeGeometry args={[pastRoom.width, pastRoom.depth]} />
        <meshStandardMaterial map={wallTexture} roughness={1} />
      </mesh>
      <pointLight
        position={[pastRoom.x, pastRoom.height - 0.3, pastRoom.z]}
        intensity={5}
        distance={9}
        decay={1.7}
        color="#e8c89a"
      />

      <Text
        position={[
          pastRoom.x,
          pastRoom.height - 0.5,
          pastRoom.z + pastRoom.depth / 2 - 0.3,
        ]}
        rotation-y={Math.PI}
        fontSize={0.22}
        color="#c8a878"
      >
        {locale === 'es' ? `ANTES · ${def.year}` : `BEFORE · ${def.year}`}
      </Text>

      <PastClutter def={def} pastRoom={pastRoom} />

      <ExitPortal
        roomIndex={pastRoom.index}
        position={[pastRoom.x, 0, pastRoom.z + pastRoom.depth / 2 - 0.6]}
        returnTo={returnTo}
      />
    </group>
  )
}
