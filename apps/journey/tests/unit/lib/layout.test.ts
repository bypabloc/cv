import { describe, expect, it } from 'vitest'
import {
  buildLayout,
  buildWallBoxes,
  CORRIDOR_HEIGHT,
  CORRIDOR_LENGTH,
  CORRIDOR_WIDTH,
  DOOR_WIDTH,
  doorBlockerBox,
  ROOM_BASE_SIZE,
  WALL_THICKNESS,
  zoneAt,
} from '../../../src/lib/layout'
import type { RoomDef } from '../../../src/lib/rooms'

function makeRoom(overrides: Partial<RoomDef>): RoomDef {
  return {
    id: 'aula',
    order: 0,
    slugs: ['iai'],
    seniority: 'intern',
    year: '2015',
    scale: 1,
    lightIntensity: 0.55,
    propDensity: 0.4,
    texts: {
      es: {
        title: 'T',
        role: 'R',
        period: '2015',
        retos: [],
        aprendizajes: [],
      },
      en: {
        title: 'T',
        role: 'R',
        period: '2015',
        retos: [],
        aprendizajes: [],
      },
    },
    ...overrides,
  }
}

const ROOMS: readonly RoomDef[] = [
  makeRoom({ id: 'aula', order: 0, scale: 1, year: '2015' }),
  makeRoom({
    id: 'cima',
    order: 1,
    scale: 1.65,
    year: '2022',
    seniority: 'lead',
  }),
]

describe('buildLayout', () => {
  it('Given 2 salas encadenadas When se construye el layout Then posiciona salas, pasillo y puerta sobre el eje Z', () => {
    const layout = buildLayout(ROOMS)

    expect(layout.rooms).toHaveLength(2)
    expect(layout.corridors).toHaveLength(1)
    expect(layout.doors).toHaveLength(1)

    // sala 0: 8x8 centrada en z=4
    expect(layout.rooms[0]).toMatchObject({
      id: 'aula',
      index: 0,
      x: 0,
      z: 4,
      width: ROOM_BASE_SIZE,
      depth: ROOM_BASE_SIZE,
      height: 3.2,
    })
    // pasillo entre 8 y 14, centrado en 11, con el año de la sala destino
    expect(layout.corridors[0]).toMatchObject({
      index: 0,
      x: 0,
      z: 11,
      width: CORRIDOR_WIDTH,
      depth: CORRIDOR_LENGTH,
      height: CORRIDOR_HEIGHT,
      year: '2022',
    })
    // puerta al final del pasillo (plano frontal de la sala 1)
    expect(layout.doors[0]).toEqual({ corridorIndex: 0, x: 0, z: 14 })
    // sala 1 escalada 1.65: 13.2 de fondo, centrada en 20.6, mas alta
    expect(layout.rooms[1]).toMatchObject({
      id: 'cima',
      index: 1,
      z: 20.6,
      width: 13.2,
      depth: 13.2,
    })
    expect(layout.rooms[1]?.height).toBeCloseTo(4.24, 10)
    expect(layout.totalDepth).toBeCloseTo(27.2, 10)
  })
})

describe('buildWallBoxes', () => {
  it('Given el layout de 2 salas When se generan los muros Then cada sala aporta 4 lados con hueco de puerta solo en el muro compartido', () => {
    const layout = buildLayout(ROOMS)
    const boxes = buildWallBoxes(layout)

    // sala 0: frontal solido (1) + trasero con hueco (2) + laterales (2) = 5
    // sala 1: frontal con hueco (2) + trasero solido (1) + laterales (2) = 5
    // pasillo: 2 laterales
    expect(boxes).toHaveLength(12)

    const room0 = boxes.filter(
      (b) => b.source.kind === 'room' && b.source.index === 0,
    )
    expect(room0).toHaveLength(5)

    // el muro trasero de la sala 0 (z=8) deja el hueco de la puerta
    const back0 = room0.filter((b) => b.minZ === 8)
    expect(back0.map((b) => [b.minX, b.maxX])).toEqual([
      [-4 - WALL_THICKNESS, -DOOR_WIDTH / 2],
      [DOOR_WIDTH / 2, 4 + WALL_THICKNESS],
    ])

    const corridor = boxes.filter((b) => b.source.kind === 'corridor')
    expect(corridor).toHaveLength(2)
    expect(corridor.map((b) => b.height)).toEqual([
      CORRIDOR_HEIGHT,
      CORRIDOR_HEIGHT,
    ])
    expect(corridor.map((b) => [b.minZ, b.maxZ])).toEqual([
      [8, 14],
      [8, 14],
    ])
  })
})

describe('doorBlockerBox', () => {
  it('Given una puerta When se genera su bloqueador Then es una caja fina centrada en el plano de la puerta', () => {
    const box = doorBlockerBox({ corridorIndex: 0, x: 0, z: 14 })

    expect(box).toEqual({
      minX: -DOOR_WIDTH / 2,
      maxX: DOOR_WIDTH / 2,
      minZ: 13.94,
      maxZ: 14.06,
    })
  })
})

describe('zoneAt', () => {
  it('Given posiciones sobre el eje Z When se resuelve la zona Then distingue sala, pasillo y clamp en los extremos', () => {
    const layout = buildLayout(ROOMS)

    expect(zoneAt(layout, 4)).toEqual({ kind: 'room', index: 0 })
    expect(zoneAt(layout, 11)).toEqual({ kind: 'corridor', index: 0 })
    expect(zoneAt(layout, 20)).toEqual({ kind: 'room', index: 1 })
    expect(zoneAt(layout, -5)).toEqual({ kind: 'room', index: 0 })
    expect(zoneAt(layout, 999)).toEqual({ kind: 'room', index: 1 })
  })
})
