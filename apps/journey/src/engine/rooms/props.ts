/**
 * @module rooms/props (engine)
 * @description Props procedurales compartidos entre salas manga-ink:
 *   escritorio, monitor con viñeta canvas, ficha (pizarra/cuaderno) con
 *   pulso, portal al pasado con swirl, portal de salida y pila de papeles.
 *   Todo primitivas del pool toon — cero .glb, cero red.
 */
import { Group, Mesh, RingGeometry } from 'three'
import { PAST_OFFSET_X, type RoomLayout } from '../../lib/layout'
import type { EngineState, FichaKind, Interactable } from '../state'
import type { RoomTheme } from '../themes'
import { boxMesh, mergedBoxes, screenPanel, toonMat, toonMatOwn } from '../toon'

export interface PropHandle {
  group: Group
  interactable?: Interactable
  update?(t: number, dt: number): void
}

/** Escritorio/mesa minima: tapa + 2 patas fusionadas (1 draw call). */
export function desk(opts: {
  position: readonly [number, number, number]
  rotationY?: number
  width?: number
  color?: string
}): Group {
  const width = opts.width ?? 1.2
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  group.add(
    mergedBoxes(
      [
        { w: width, h: 0.05, d: 0.6, x: 0, y: 0.72, z: 0 },
        { w: 0.06, h: 0.72, d: 0.55, x: -width / 2 + 0.05, y: 0.36, z: 0 },
        { w: 0.06, h: 0.72, d: 0.55, x: width / 2 - 0.05, y: 0.36, z: 0 },
      ],
      toonMat(opts.color ?? '#4a4038'),
    ),
  )
  return group
}

/** Monitor sobre pie con pantalla-viñeta canvas. */
export function monitor(opts: {
  position: readonly [number, number, number]
  rotationY?: number
  lines: readonly string[]
  title?: string
  theme: Pick<RoomTheme, 'screenBg' | 'screenFg' | 'ink'>
  width?: number
}): Group {
  const width = opts.width ?? 0.6
  const height = width * 0.6
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // pie + marco fusionados (1 draw call)
  const body = mergedBoxes(
    [
      { w: 0.16, h: 0.14, d: 0.16, x: 0, y: 0.07, z: 0 },
      {
        w: width + 0.05,
        h: height + 0.05,
        d: 0.05,
        x: 0,
        y: height / 2 + 0.14,
        z: -0.02,
      },
    ],
    toonMat('#15151a'),
  )
  body.userData.noOutline = true
  const screen = screenPanel({
    lines: opts.lines,
    title: opts.title,
    theme: opts.theme,
    width,
    height,
  })
  screen.position.set(0, height / 2 + 0.14, 0.01)
  group.add(body, screen)
  return group
}

const FICHA_LABELS: Record<FichaKind, Record<'es' | 'en', string>> = {
  retos: { es: 'Leer los retos', en: 'Read the challenges' },
  aprendizajes: { es: 'Leer los aprendizajes', en: 'Read the learnings' },
}

/**
 * Objeto focal de RETOS (pizarra) o APRENDIZAJES (cuaderno): E abre la
 * ficha HTML del HUD. Pulsa el emissive cuando es el interactable activo.
 */
export function fichaProp(opts: {
  roomIndex: number
  kind: FichaKind
  style: 'pizarra' | 'cuaderno'
  position: readonly [number, number, number]
  rotationY?: number
  accent: string
  state: EngineState
  onOpen(roomIndex: number, kind: FichaKind): void
}): PropHandle {
  const id = `ficha-${opts.roomIndex}-${opts.kind}`
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // material propio: el pulso muta emissiveIntensity (no va al pool)
  const pulseMat = toonMatOwn(
    opts.style === 'pizarra' ? '#2e4d3a' : '#f2ead8',
    { emissive: opts.accent, emissiveIntensity: 0.12 },
  )
  if (opts.style === 'pizarra') {
    const board = boxMesh(1.9, 1.2, 0.06, pulseMat)
    board.position.set(0, 1.6, 0)
    const backing = boxMesh(2.05, 1.35, 0.04, toonMat('#5a4632'))
    backing.position.set(0, 1.6, -0.05)
    backing.userData.noOutline = true
    group.add(board, backing)
  } else {
    const podium = boxMesh(0.42, 1, 0.42, toonMat('#4a3b2a'))
    podium.position.set(0, 0.5, 0)
    const pageL = boxMesh(0.3, 0.03, 0.42, pulseMat)
    pageL.position.set(-0.14, 1.03, 0)
    pageL.rotation.z = 0.16
    pageL.userData.noOutline = true
    const pageR = boxMesh(0.3, 0.03, 0.42, toonMat('#e8dfc8'))
    pageR.position.set(0.14, 1.03, 0)
    pageR.rotation.z = -0.16
    pageR.userData.noOutline = true
    group.add(podium, pageL, pageR)
  }
  return {
    group,
    interactable: {
      id,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2.2,
      label: FICHA_LABELS[opts.kind],
      onActivate: () => opts.onOpen(opts.roomIndex, opts.kind),
    },
    update: (t) => {
      pulseMat.emissiveIntensity =
        opts.state.activeId === id ? 0.45 + Math.sin(t * 5) * 0.2 : 0.12
    },
  }
}

const PORTAL_LABEL = {
  es: 'Cruzar al pasado',
  en: 'Step into the past',
} as const

const EXIT_LABEL = {
  es: 'Volver al presente',
  en: 'Return to the present',
} as const

/** Puerta-portal al "antes" de la sala (teleporta a la sala espejo). */
export function pastPortal(opts: {
  room: RoomLayout
  position: readonly [number, number, number]
  rotationY?: number
  accent: string
  onEnter(roomIndex: number, spawn: { x: number; z: number }): void
}): PropHandle {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  const frame = boxMesh(1.3, 2.1, 0.08, toonMat('#141018'))
  frame.position.set(0, 1.05, 0)
  const swirlGeo = new RingGeometry(0.32, 0.55, 24)
  const swirl = new Mesh(
    swirlGeo,
    toonMatOwn(opts.accent, {
      emissive: opts.accent,
      emissiveIntensity: 1.1,
      transparent: true,
      opacity: 0.85,
    }),
  )
  swirl.position.set(0, 1.05, 0.06)
  swirl.userData.noOutline = true
  const header = boxMesh(
    1.5,
    0.16,
    0.12,
    toonMat(opts.accent, { emissive: opts.accent, emissiveIntensity: 0.5 }),
  )
  header.position.set(0, 2.28, 0)
  header.userData.noOutline = true
  group.add(frame, swirl, header)
  return {
    group,
    interactable: {
      id: `portal-${opts.room.index}`,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2,
      label: PORTAL_LABEL,
      onActivate: () =>
        opts.onEnter(opts.room.index, {
          x: PAST_OFFSET_X,
          z: opts.room.z + 1.6,
        }),
    },
    update: (t) => {
      swirl.rotation.z = t * 0.9
    },
  }
}

/** Portal de salida dentro de la mini-sala del pasado. */
export function exitPortal(opts: {
  roomIndex: number
  position: readonly [number, number, number]
  onExit(): void
}): PropHandle {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  const frame = boxMesh(
    1.3,
    2.1,
    0.08,
    toonMat('#1a1a22', { emissive: '#8fd4ff', emissiveIntensity: 0.4 }),
  )
  frame.position.set(0, 1.05, 0)
  group.add(frame)
  return {
    group,
    interactable: {
      id: `portal-exit-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2,
      label: EXIT_LABEL,
      onActivate: () => opts.onExit(),
    },
  }
}

/** Pila de papeles: laminas fusionadas en 1 mesh, desorden determinista. */
export function paperStack(opts: {
  position: readonly [number, number, number]
  count?: number
}): Group {
  const count = opts.count ?? 8
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  const stack = mergedBoxes(
    Array.from({ length: count }, (_, i) => ({
      w: 0.3,
      h: 0.012,
      d: 0.42,
      x: 0,
      y: 0.012 * i,
      z: 0,
      rotY: Math.sin(i * 2.3) * 0.25,
    })),
    toonMat('#e8e2d0'),
  )
  stack.userData.noOutline = true
  group.add(stack)
  return group
}
