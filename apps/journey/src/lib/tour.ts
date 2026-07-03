/**
 * @module tour
 * @description Riel del tour guiado (tier Reduced / movil): la camara
 *   recorre sola los centros de sala pasando por las puertas, con pausa en
 *   cada etapa para leer los textos. Puro y muestreable por tiempo — el
 *   componente GuidedTour solo aplica la pose al camera.
 *
 * @see docs/specs/journey-3d-cv/07-implementacion-mvp.md (AC-10)
 */
import type { JourneyLayout } from './layout'
import { zoneAt } from './layout'

export interface TourStop {
  x: number
  z: number
  /** Segundos detenido en el stop (0 = pasa de largo). */
  pause: number
  /** Indice de sala si el stop es el centro de una sala. */
  roomIndex?: number
}

export interface TourTimeline {
  stops: TourStop[]
  /** Momento (seg) en que la camara LLEGA a cada stop. */
  arrivals: number[]
  total: number
  speed: number
}

export interface TourPose {
  x: number
  z: number
  lookX: number
  lookZ: number
  roomIndex: number
}

interface TourOptions {
  /** m/s del paseo. */
  speed?: number
  /** Segundos de pausa en el centro de cada sala. */
  pause?: number
}

/** Stops: centro de cada sala (pausa) + el plano de cada puerta (pasa). */
function buildTourStops(layout: JourneyLayout, pause: number): TourStop[] {
  const stops: TourStop[] = []
  layout.rooms.forEach((room, i) => {
    stops.push({ x: room.x, z: room.z, pause, roomIndex: i })
    const door = layout.doors[i]
    if (door) {
      stops.push({ x: door.x, z: door.z, pause: 0 })
    }
  })
  return stops
}

export function buildTourTimeline(
  layout: JourneyLayout,
  options: TourOptions = {},
): TourTimeline {
  const speed = options.speed ?? 1.4
  const pause = options.pause ?? 7
  const stops = buildTourStops(layout, pause)
  const arrivals: number[] = []
  let t = 0
  stops.forEach((stop, i) => {
    if (i === 0) {
      arrivals.push(0)
      t = stop.pause
      return
    }
    const prev = stops[i - 1]
    if (prev) {
      t += Math.hypot(stop.x - prev.x, stop.z - prev.z) / speed
    }
    arrivals.push(t)
    t += stop.pause
  })
  return { stops, arrivals, total: t, speed }
}

/**
 * @function tourPoseAt
 * @description Pose de camara del riel en el segundo `tSec` (loopea).
 *   Durante una pausa mira al siguiente stop; durante un tramo, al destino.
 */
export function tourPoseAt(timeline: TourTimeline, tSec: number): TourPose {
  const { stops, arrivals, total } = timeline
  const first = stops[0]
  if (!first || total <= 0) {
    return { x: 0, z: 0, lookX: 0, lookZ: 1, roomIndex: 0 }
  }
  const t = ((tSec % total) + total) % total

  for (let i = stops.length - 1; i >= 0; i -= 1) {
    const stop = stops[i]
    const arrival = arrivals[i]
    if (!stop || arrival === undefined || t < arrival) {
      continue
    }
    const next = stops[i + 1]
    const look = next ?? { x: stop.x, z: stop.z + 1 }
    // en pausa sobre el stop
    if (t <= arrival + stop.pause || !next) {
      return {
        x: stop.x,
        z: stop.z,
        lookX: look.x,
        lookZ: look.z,
        roomIndex: resolveRoomIndex(stop, timeline, i),
      }
    }
    // caminando hacia el siguiente
    const nextArrival = arrivals[i + 1]
    if (nextArrival === undefined) {
      continue
    }
    const k = (t - arrival - stop.pause) / (nextArrival - arrival - stop.pause)
    return {
      x: stop.x + (next.x - stop.x) * k,
      z: stop.z + (next.z - stop.z) * k,
      lookX: next.x,
      lookZ: next.z,
      roomIndex: resolveRoomIndex(stop, timeline, i),
    }
  }
  return {
    x: first.x,
    z: first.z,
    lookX: first.x,
    lookZ: first.z + 1,
    roomIndex: 0,
  }
}

function resolveRoomIndex(
  stop: TourStop,
  timeline: TourTimeline,
  index: number,
): number {
  if (stop.roomIndex !== undefined) {
    return stop.roomIndex
  }
  // stop de puerta: hereda la sala previa
  for (let i = index; i >= 0; i -= 1) {
    const prev = timeline.stops[i]
    if (prev?.roomIndex !== undefined) {
      return prev.roomIndex
    }
  }
  return 0
}

/** Tiempo del riel en el que la camara llega al centro de una sala. */
export function tourTimeForRoom(
  timeline: TourTimeline,
  roomIndex: number,
): number {
  const i = timeline.stops.findIndex((s) => s.roomIndex === roomIndex)
  return i >= 0 ? (timeline.arrivals[i] ?? 0) : 0
}

/** Zona reportable del pose (para HUD/audio/lazy-load). */
export function tourZoneAt(layout: JourneyLayout, pose: TourPose) {
  return zoneAt(layout, pose.z)
}
