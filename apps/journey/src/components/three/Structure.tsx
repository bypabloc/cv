/**
 * @component Structure
 * @description Estructura procedural del recorrido: muros (las MISMAS cajas
 *   que los colisionadores), pisos, techos, dinteles sobre las puertas y la
 *   luz base por sala/pasillo. El eje seniority se ve aqui: cada sala usa
 *   la paleta de su rubro y la `lightIntensity` de su RoomDef, y su tamaño
 *   ya viene escalado del layout.
 */
import { Text } from '@react-three/drei'
import { useMemo } from 'react'
import type { CanvasTexture } from 'three'
import {
  CORRIDOR_HEIGHT,
  DOOR_HEIGHT,
  DOOR_WIDTH,
  type JourneyLayout,
  WALL_THICKNESS,
  type WallBox,
} from '../../lib/layout'
import type { RoomDef, RoomId } from '../../lib/rooms'
import { PALETTES } from './rooms/palettes'
import { plasterTexture, tileTexture } from './textures'

interface StructureProps {
  layout: JourneyLayout
  rooms: readonly RoomDef[]
  walls: readonly WallBox[]
}

interface HeaderBox {
  key: string
  x: number
  y: number
  z: number
  width: number
  height: number
  depth: number
}

/** Dinteles: rellenan el hueco de puerta desde DOOR_HEIGHT hasta el techo. */
function buildHeaders(layout: JourneyLayout): HeaderBox[] {
  const headers: HeaderBox[] = []
  for (const door of layout.doors) {
    const roomBefore = layout.rooms[door.corridorIndex]
    const roomAfter = layout.rooms[door.corridorIndex + 1]
    if (!roomBefore || !roomAfter) {
      continue
    }
    const backZ = roomBefore.z + roomBefore.depth / 2
    headers.push({
      key: `header-back-${door.corridorIndex}`,
      x: 0,
      y: (roomBefore.height + DOOR_HEIGHT) / 2,
      z: backZ + WALL_THICKNESS / 2,
      width: DOOR_WIDTH,
      height: roomBefore.height - DOOR_HEIGHT,
      depth: WALL_THICKNESS,
    })
    const frontZ = roomAfter.z - roomAfter.depth / 2
    headers.push({
      key: `header-front-${door.corridorIndex}`,
      x: 0,
      y: (roomAfter.height + DOOR_HEIGHT) / 2,
      z: frontZ - WALL_THICKNESS / 2,
      width: DOOR_WIDTH,
      height: roomAfter.height - DOOR_HEIGHT,
      depth: WALL_THICKNESS,
    })
  }
  return headers
}

interface RoomTextures {
  wall: CanvasTexture
  floor: CanvasTexture
}

export function Structure({ layout, rooms, walls }: StructureProps) {
  const corridorTexture = useMemo(
    () => plasterTexture('#2b2b33', '#9fb4ff', 13),
    [],
  )
  const ceilingTexture = useMemo(
    () => plasterTexture('#202027', '#000000', 5),
    [],
  )
  const roomTextures = useMemo(() => {
    const map: Partial<Record<RoomId, RoomTextures>> = {}
    for (const def of rooms) {
      const pal = PALETTES[def.id]
      map[def.id] = {
        wall: plasterTexture(pal.wall, pal.wallSpeck, 7 + def.order),
        floor: tileTexture(pal.floor, pal.floorLine, 5, 11 + def.order),
      }
    }
    return map
  }, [rooms])
  const headers = useMemo(() => buildHeaders(layout), [layout])

  const wallTextureFor = (wall: WallBox): CanvasTexture => {
    if (wall.source.kind === 'room') {
      const id = layout.rooms[wall.source.index]?.id
      const textures = id ? roomTextures[id] : undefined
      if (textures) {
        return textures.wall
      }
    }
    return corridorTexture
  }

  return (
    <group>
      {walls
        .filter((wall) => wall.source.kind !== 'past')
        .map((wall) => {
          const width = wall.maxX - wall.minX
          const depth = wall.maxZ - wall.minZ
          return (
            <mesh
              key={`wall-${wall.minX}:${wall.maxX}:${wall.minZ}:${wall.maxZ}`}
              position={[
                (wall.minX + wall.maxX) / 2,
                wall.height / 2,
                (wall.minZ + wall.maxZ) / 2,
              ]}
              receiveShadow
            >
              <boxGeometry args={[width, wall.height, depth]} />
              <meshStandardMaterial
                map={wallTextureFor(wall)}
                roughness={0.95}
              />
            </mesh>
          )
        })}

      {headers.map((h) => (
        <mesh key={h.key} position={[h.x, h.y, h.z]}>
          <boxGeometry args={[h.width, h.height, h.depth]} />
          <meshStandardMaterial map={corridorTexture} roughness={0.95} />
        </mesh>
      ))}

      {layout.rooms.map((room) => {
        const def = rooms[room.index]
        const pal = PALETTES[room.id]
        const intensity = def ? def.lightIntensity : 0.6
        const textures = roomTextures[room.id]
        return (
          <group key={`room-${room.id}`}>
            <mesh
              rotation-x={-Math.PI / 2}
              position={[room.x, 0, room.z]}
              receiveShadow
            >
              <planeGeometry args={[room.width, room.depth]} />
              <meshStandardMaterial
                map={textures ? textures.floor : corridorTexture}
                roughness={0.9}
              />
            </mesh>
            <mesh
              rotation-x={Math.PI / 2}
              position={[room.x, room.height, room.z]}
            >
              <planeGeometry args={[room.width, room.depth]} />
              <meshStandardMaterial map={ceilingTexture} roughness={1} />
            </mesh>
            <pointLight
              position={[room.x, room.height - 0.35, room.z]}
              intensity={14 * intensity}
              distance={room.width * 2.2}
              decay={1.6}
              castShadow={false}
              color={pal.lightColor}
            />
          </group>
        )
      })}

      {layout.corridors.map((corridor) => (
        <group key={`corridor-${corridor.index}`}>
          <mesh
            rotation-x={-Math.PI / 2}
            position={[corridor.x, 0, corridor.z]}
          >
            <planeGeometry args={[corridor.width, corridor.depth]} />
            <meshStandardMaterial map={corridorTexture} roughness={0.9} />
          </mesh>
          <mesh
            rotation-x={Math.PI / 2}
            position={[corridor.x, CORRIDOR_HEIGHT, corridor.z]}
          >
            <planeGeometry args={[corridor.width, corridor.depth]} />
            <meshStandardMaterial map={ceilingTexture} roughness={1} />
          </mesh>
          <pointLight
            position={[corridor.x, CORRIDOR_HEIGHT - 0.25, corridor.z]}
            intensity={4}
            distance={corridor.depth * 1.6}
            decay={1.7}
            color="#cfd8ff"
          />
          {/* mini-timeline del pasillo: el año de la etapa destino en el piso */}
          <Text
            position={[corridor.x, 0.02, corridor.z]}
            rotation={[-Math.PI / 2, 0, 0]}
            fontSize={0.7}
            color="#8fa3c8"
            anchorX="center"
            anchorY="middle"
          >
            {corridor.year}
          </Text>
        </group>
      ))}
    </group>
  )
}
