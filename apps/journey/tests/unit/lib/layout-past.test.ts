import { describe, expect, it } from 'vitest'
import {
  buildLayout,
  buildPastRooms,
  buildPastWallBoxes,
  PAST_OFFSET_X,
  PAST_ROOM_HEIGHT,
  PAST_ROOM_SIZE,
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
  makeRoom({ id: 'cima', order: 1, scale: 1.65, year: '2022' }),
]

describe('buildPastRooms', () => {
  it('Given el layout When se construyen las salas del pasado Then hay una por sala, desplazada en X y alineada en Z', () => {
    const layout = buildLayout(ROOMS)
    const past = buildPastRooms(layout)

    expect(past).toHaveLength(2)
    expect(past[0]).toEqual({
      index: 0,
      x: PAST_OFFSET_X,
      z: 4,
      width: PAST_ROOM_SIZE,
      depth: PAST_ROOM_SIZE,
      height: PAST_ROOM_HEIGHT,
    })
    expect(past[1]?.x).toBe(PAST_OFFSET_X)
    expect(past[1]?.z).toBe(20.6)
  })
})

describe('buildPastWallBoxes', () => {
  it('Given las salas del pasado When se generan sus muros Then son 4 muros solidos por sala sin huecos', () => {
    const layout = buildLayout(ROOMS)
    const boxes = buildPastWallBoxes(buildPastRooms(layout))

    expect(boxes).toHaveLength(8)
    expect(boxes.every((b) => b.source.kind === 'past')).toBe(true)
    expect(boxes.every((b) => b.height === PAST_ROOM_HEIGHT)).toBe(true)

    // los 4 muros de la sala 0 encierran el cuadrado [37,43]x[1,7]
    const room0 = boxes.filter((b) => b.source.index === 0)
    expect(room0).toHaveLength(4)
    const minX = Math.min(...room0.map((b) => b.minX))
    const maxX = Math.max(...room0.map((b) => b.maxX))
    expect(minX).toBe(PAST_OFFSET_X - PAST_ROOM_SIZE / 2 - 0.2)
    expect(maxX).toBe(PAST_OFFSET_X + PAST_ROOM_SIZE / 2 + 0.2)
  })
})
