/**
 * @module layout
 * @description Geometria del recorrido (Propuesta A): salas encadenadas sobre
 *   el eje +Z, conectadas por pasillos con una puerta al final de cada uno.
 *   Es la UNICA fuente de verdad espacial: los muros visuales y los
 *   colisionadores AABB se derivan de las mismas cajas (`buildWallBoxes`).
 *
 * @see docs/specs/journey-3d-cv/07-implementacion-mvp.md
 */
import type { Box2 } from './collision'
import type { RoomDef, RoomId } from './rooms'

export const ROOM_BASE_SIZE = 8
export const ROOM_HEIGHT_BASE = 3.2
export const CORRIDOR_WIDTH = 2.4
export const CORRIDOR_LENGTH = 6
export const CORRIDOR_HEIGHT = 2.6
export const DOOR_WIDTH = 1.4
export const DOOR_HEIGHT = 2.1
export const WALL_THICKNESS = 0.2
export const EYE_HEIGHT = 1.65
export const PLAYER_RADIUS = 0.35
export const WALK_SPEED = 3.5

export interface RoomLayout {
  id: RoomId
  index: number
  x: number
  z: number
  width: number
  depth: number
  height: number
}

export interface CorridorLayout {
  index: number
  x: number
  z: number
  width: number
  depth: number
  height: number
  /** Año de la sala DESTINO (mini-timeline del pasillo). */
  year: string
}

export interface DoorLayout {
  corridorIndex: number
  x: number
  z: number
}

export interface JourneyLayout {
  rooms: RoomLayout[]
  corridors: CorridorLayout[]
  doors: DoorLayout[]
  totalDepth: number
}

/** La altura crece con el seniority, a la mitad del ritmo de la planta. */
function roomHeight(scale: number): number {
  return ROOM_HEIGHT_BASE * (1 + (scale - 1) / 2)
}

/**
 * @function buildLayout
 * @description Encadena las salas sobre +Z: [sala][pasillo][sala]...
 *   La puerta de cada pasillo vive en su extremo final (el plano frontal de
 *   la sala siguiente) — el pasillo es el "pasillo de carga" del plan.
 */
export function buildLayout(rooms: readonly RoomDef[]): JourneyLayout {
  const roomLayouts: RoomLayout[] = []
  const corridors: CorridorLayout[] = []
  const doors: DoorLayout[] = []
  let cursor = 0

  rooms.forEach((room, index) => {
    const size = ROOM_BASE_SIZE * room.scale
    roomLayouts.push({
      id: room.id,
      index,
      x: 0,
      z: cursor + size / 2,
      width: size,
      depth: size,
      height: roomHeight(room.scale),
    })
    cursor += size

    const next = rooms[index + 1]
    if (next) {
      corridors.push({
        index,
        x: 0,
        z: cursor + CORRIDOR_LENGTH / 2,
        width: CORRIDOR_WIDTH,
        depth: CORRIDOR_LENGTH,
        height: CORRIDOR_HEIGHT,
        year: next.year,
      })
      cursor += CORRIDOR_LENGTH
      doors.push({ corridorIndex: index, x: 0, z: cursor })
    }
  })

  return { rooms: roomLayouts, corridors, doors, totalDepth: cursor }
}

export interface WallBox extends Box2 {
  height: number
  source: { kind: 'room' | 'corridor' | 'past'; index: number }
}

interface WallSegmentInput {
  minZ: number
  maxZ: number
  fromX: number
  toX: number
  height: number
  source: WallBox['source']
}

function segment(input: WallSegmentInput): WallBox {
  return {
    minX: input.fromX,
    maxX: input.toX,
    minZ: input.minZ,
    maxZ: input.maxZ,
    height: input.height,
    source: input.source,
  }
}

/** Muro frontal/trasero: solido, o partido en 2 si tiene hueco de puerta. */
function crossWall(
  z: number,
  halfWidth: number,
  height: number,
  withOpening: boolean,
  source: WallBox['source'],
): WallBox[] {
  const base = { minZ: z, maxZ: z + WALL_THICKNESS, height, source }
  const outer = halfWidth + WALL_THICKNESS
  if (!withOpening) {
    return [segment({ ...base, fromX: -outer, toX: outer })]
  }
  return [
    segment({ ...base, fromX: -outer, toX: -DOOR_WIDTH / 2 }),
    segment({ ...base, fromX: DOOR_WIDTH / 2, toX: outer }),
  ]
}

/**
 * @function buildWallBoxes
 * @description Deriva TODOS los muros (visual + colision) del layout.
 *   Frontal/trasero de cada sala con hueco de puerta solo donde conecta un
 *   pasillo; laterales solidos; pasillos con sus 2 laterales.
 */
export function buildWallBoxes(layout: JourneyLayout): WallBox[] {
  const boxes: WallBox[] = []

  for (const room of layout.rooms) {
    const half = room.width / 2
    const zFront = room.z - room.depth / 2
    const zBack = room.z + room.depth / 2
    const source = { kind: 'room' as const, index: room.index }
    const hasFrontOpening = room.index > 0
    const hasBackOpening = room.index < layout.rooms.length - 1

    // frontal (hacia -Z): el muro ocupa la franja EXTERIOR [zFront - t, zFront]
    for (const box of crossWall(
      zFront - WALL_THICKNESS,
      half,
      room.height,
      hasFrontOpening,
      source,
    )) {
      boxes.push(box)
    }
    // trasero (hacia +Z): franja exterior [zBack, zBack + t]
    for (const box of crossWall(
      zBack,
      half,
      room.height,
      hasBackOpening,
      source,
    )) {
      boxes.push(box)
    }
    // laterales solidos (cubren las esquinas extendiendose t a cada lado)
    boxes.push(
      segment({
        minZ: zFront - WALL_THICKNESS,
        maxZ: zBack + WALL_THICKNESS,
        fromX: -half - WALL_THICKNESS,
        toX: -half,
        height: room.height,
        source,
      }),
      segment({
        minZ: zFront - WALL_THICKNESS,
        maxZ: zBack + WALL_THICKNESS,
        fromX: half,
        toX: half + WALL_THICKNESS,
        height: room.height,
        source,
      }),
    )
  }

  for (const corridor of layout.corridors) {
    const half = corridor.width / 2
    const zStart = corridor.z - corridor.depth / 2
    const zEnd = corridor.z + corridor.depth / 2
    const source = { kind: 'corridor' as const, index: corridor.index }
    boxes.push(
      segment({
        minZ: zStart,
        maxZ: zEnd,
        fromX: -half - WALL_THICKNESS,
        toX: -half,
        height: corridor.height,
        source,
      }),
      segment({
        minZ: zStart,
        maxZ: zEnd,
        fromX: half,
        toX: half + WALL_THICKNESS,
        height: corridor.height,
        source,
      }),
    )
  }

  return boxes
}

/** Caja fina que bloquea el paso mientras la puerta esta cerrada. */
export function doorBlockerBox(door: DoorLayout): Box2 {
  return {
    minX: door.x - DOOR_WIDTH / 2,
    maxX: door.x + DOOR_WIDTH / 2,
    minZ: door.z - 0.06,
    maxZ: door.z + 0.06,
  }
}

export interface Zone {
  kind: 'room' | 'corridor'
  index: number
}

/**
 * @function zoneAt
 * @description Resuelve en que sala/pasillo cae una coordenada Z.
 *   Fuera del recorrido, clampa a la primera/ultima sala.
 */
export function zoneAt(layout: JourneyLayout, z: number): Zone {
  for (const room of layout.rooms) {
    if (z >= room.z - room.depth / 2 && z <= room.z + room.depth / 2) {
      return { kind: 'room', index: room.index }
    }
  }
  for (const corridor of layout.corridors) {
    if (
      z >= corridor.z - corridor.depth / 2 &&
      z <= corridor.z + corridor.depth / 2
    ) {
      return { kind: 'corridor', index: corridor.index }
    }
  }
  return { kind: 'room', index: z < 0 ? 0 : layout.rooms.length - 1 }
}

export const PAST_OFFSET_X = 40
export const PAST_ROOM_SIZE = 6
export const PAST_ROOM_HEIGHT = 2.7

export interface PastRoomLayout {
  index: number
  x: number
  z: number
  width: number
  depth: number
  height: number
}

/**
 * @function buildPastRooms
 * @description Una mini-sala "antes" por sala, desplazada PAST_OFFSET_X en X
 *   y alineada en Z con su sala (asi zoneAt sigue reportando la sala
 *   correcta mientras se visita el pasado). Se entra/sale por teleport
 *   (portal), no por puertas: sus 4 muros son solidos.
 */
export function buildPastRooms(layout: JourneyLayout): PastRoomLayout[] {
  return layout.rooms.map((room) => ({
    index: room.index,
    x: PAST_OFFSET_X,
    z: room.z,
    width: PAST_ROOM_SIZE,
    depth: PAST_ROOM_SIZE,
    height: PAST_ROOM_HEIGHT,
  }))
}

export function buildPastWallBoxes(
  pastRooms: readonly PastRoomLayout[],
): WallBox[] {
  const boxes: WallBox[] = []
  for (const past of pastRooms) {
    const half = past.width / 2
    const zFront = past.z - past.depth / 2
    const zBack = past.z + past.depth / 2
    const source = { kind: 'past' as const, index: past.index }
    const outerL = past.x - half - WALL_THICKNESS
    const outerR = past.x + half + WALL_THICKNESS
    boxes.push(
      // frontal / trasero
      {
        minX: outerL,
        maxX: outerR,
        minZ: zFront - WALL_THICKNESS,
        maxZ: zFront,
        height: past.height,
        source,
      },
      {
        minX: outerL,
        maxX: outerR,
        minZ: zBack,
        maxZ: zBack + WALL_THICKNESS,
        height: past.height,
        source,
      },
      // laterales
      {
        minX: outerL,
        maxX: past.x - half,
        minZ: zFront,
        maxZ: zBack,
        height: past.height,
        source,
      },
      {
        minX: past.x + half,
        maxX: outerR,
        minZ: zFront,
        maxZ: zBack,
        height: past.height,
        source,
      },
    )
  }
  return boxes
}
