import { describe, expect, it } from 'vitest'
import { buildLayout } from '../../../src/lib/layout'
import type { RoomDef } from '../../../src/lib/rooms'
import {
  buildTourTimeline,
  tourPoseAt,
  tourTimeForRoom,
  tourZoneAt,
} from '../../../src/lib/tour'

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

// salas de 8 y 13.2: centros en z=4 y z=20.6, puerta en z=14
const LAYOUT = buildLayout([
  makeRoom({ id: 'aula', order: 0, scale: 1 }),
  makeRoom({ id: 'cima', order: 1, scale: 1.65 }),
])

// speed=2 y pause=6 dan tiempos redondos: 4->14 = 5s, 14->20.6 = 3.3s
const TIMELINE = buildTourTimeline(LAYOUT, { speed: 2, pause: 6 })

describe('buildTourTimeline', () => {
  it('Given 2 salas When se construye el riel Then para en cada centro de sala y cruza la puerta', () => {
    expect(TIMELINE.stops.map((s) => [s.x, s.z, s.pause, s.roomIndex])).toEqual(
      [
        [0, 4, 6, 0],
        [0, 14, 0, undefined],
        [0, 20.6, 6, 1],
      ],
    )
    // llegadas: sala0 en t=0; puerta en 6+5=11; sala1 en 11+3.3=14.3
    expect(TIMELINE.arrivals).toEqual([0, 11, 14.3])
    // total = llegada final + su pausa
    expect(TIMELINE.total).toBeCloseTo(20.3, 10)
  })
})

describe('tourPoseAt', () => {
  it('Given t dentro de la pausa inicial When se muestrea Then la camara esta quieta en la sala 0 mirando a la puerta', () => {
    const pose = tourPoseAt(TIMELINE, 3)

    expect(pose.x).toBe(0)
    expect(pose.z).toBe(4)
    expect(pose.lookZ).toBe(14)
    expect(pose.roomIndex).toBe(0)
  })

  it('Given t a mitad del primer tramo When se muestrea Then avanza linealmente hacia la puerta', () => {
    // tramo 6..11: en t=8.5 va 50% -> z=9
    const pose = tourPoseAt(TIMELINE, 8.5)

    expect(pose.z).toBeCloseTo(9, 10)
    expect(pose.lookZ).toBe(14)
  })

  it('Given t en la pausa de la ultima sala When se muestrea Then esta en su centro y reporta su indice', () => {
    const pose = tourPoseAt(TIMELINE, 15)

    expect(pose.z).toBeCloseTo(20.6, 10)
    expect(pose.roomIndex).toBe(1)
  })

  it('Given t mayor al total When se muestrea Then el riel loopea (modulo)', () => {
    const pose = tourPoseAt(TIMELINE, TIMELINE.total + 3)

    expect(pose.z).toBe(4)
    expect(pose.roomIndex).toBe(0)
  })
})

describe('tourTimeForRoom', () => {
  it('Given un indice de sala When se resuelve su tiempo Then es la llegada de su stop', () => {
    expect(tourTimeForRoom(TIMELINE, 0)).toBe(0)
    expect(tourTimeForRoom(TIMELINE, 1)).toBeCloseTo(14.3, 10)
  })

  it('Given un indice inexistente When se resuelve Then retorna 0', () => {
    expect(tourTimeForRoom(TIMELINE, 9)).toBe(0)
  })
})

describe('tramos que heredan la sala previa', () => {
  it('Given t caminando desde la puerta hacia la sala 1 When se muestrea Then reporta la sala previa (0)', () => {
    // la puerta (llegada t=11, pausa 0) no tiene roomIndex: se hereda
    const pose = tourPoseAt(TIMELINE, 12)

    expect(pose.roomIndex).toBe(0)
    expect(pose.z).toBeCloseTo(16, 10)
  })
})

describe('tourZoneAt', () => {
  it('Given un pose dentro del pasillo When se resuelve la zona Then es corridor 0', () => {
    const pose = tourPoseAt(TIMELINE, 9.5)

    expect(pose.z).toBeCloseTo(11, 10)
    expect(tourZoneAt(LAYOUT, pose)).toEqual({ kind: 'corridor', index: 0 })
  })
})

describe('timeline vacio', () => {
  it('Given un layout sin salas When se muestrea Then retorna el pose neutro', () => {
    const empty = buildTourTimeline(buildLayout([]))

    expect(tourPoseAt(empty, 5)).toEqual({
      x: 0,
      z: 0,
      lookX: 0,
      lookZ: 1,
      roomIndex: 0,
    })
  })
})
