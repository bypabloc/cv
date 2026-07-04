/**
 * @module rooms/props (engine)
 * @description Props procedurales compartidos entre salas manga-ink:
 *   escritorio, monitor (estatico e intercambiable), pizarra de ficha con
 *   titulo + tiza, portal al pasado con swirl, portal de salida y pila de
 *   papeles. Todo primitivas del pool toon — cero .glb, cero red.
 */
import {
  type CanvasTexture,
  CircleGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
} from 'three'
import type { Box2 } from '../../lib/collision'
import { PAST_OFFSET_X, type RoomLayout } from '../../lib/layout'
import type { Locale } from '../../lib/rooms'
import type { EngineState, FichaKind, Interactable } from '../state'
import type { RoomTheme } from '../themes'
import {
  basicMat,
  boxMesh,
  label,
  makeCanvasTexture,
  makeRng,
  mergedBoxes,
  type ScreenPanelOpts,
  screenPanel,
  screenTexture,
  toonMat,
  toonMatOwn,
  unitGeo,
} from '../toon'

export interface PropHandle {
  group: Group
  interactable?: Interactable
  update?(t: number, dt: number): void
}

/** AABB de piso para un prop (collider de contenido). */
export function footprint(x: number, z: number, w: number, d: number): Box2 {
  return {
    minX: x - w / 2,
    maxX: x + w / 2,
    minZ: z - d / 2,
    maxZ: z + d / 2,
  }
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

const FICHA_TITLES: Record<FichaKind, Record<Locale, string>> = {
  retos: { es: 'RETOS', en: 'CHALLENGES' },
  aprendizajes: { es: 'APRENDIZAJES', en: 'LEARNINGS' },
}

/** Tiza sobre pizarra: titulo grande subrayado + bullets del CV. */
function chalkTexture(opts: {
  title: string
  bullets: readonly string[]
  theme: RoomTheme
}): CanvasTexture {
  const rng = makeRng(opts.title.length * 31 + opts.bullets.length)
  return makeCanvasTexture(512, (ctx, size) => {
    ctx.fillStyle = opts.theme.screenBg
    ctx.fillRect(0, 0, size, size)
    // borde de tiza irregular
    ctx.strokeStyle = '#e8e4d4'
    ctx.lineCap = 'round'
    ctx.globalAlpha = 0.5
    ctx.lineWidth = 4
    ctx.strokeRect(12, 12, size - 24, size - 24)
    ctx.globalAlpha = 1
    // titulo grande + subrayado con el acento de la sala
    ctx.fillStyle = '#f2eedd'
    ctx.font = `bold 58px ${'"Space Grotesk", system-ui, sans-serif'}`
    ctx.fillText(opts.title, 36, 96)
    ctx.strokeStyle = opts.theme.accent
    ctx.lineWidth = 6
    ctx.beginPath()
    ctx.moveTo(36, 118)
    ctx.lineTo(36 + Math.min(420, opts.title.length * 34), 118 + rng() * 3)
    ctx.stroke()
    // bullets cortos (el detalle completo vive en el panel DOM con E)
    ctx.fillStyle = '#e8e4d4'
    ctx.font = '26px "Space Grotesk", system-ui, sans-serif'
    let y = 190
    for (const bullet of opts.bullets.slice(0, 3)) {
      const text = bullet.length > 34 ? `${bullet.slice(0, 33)}…` : bullet
      ctx.fillText(`· ${text}`, 36, y)
      y += 88
    }
    // hint de interaccion escrito con tiza chica
    ctx.globalAlpha = 0.55
    ctx.font = '22px "Space Mono", ui-monospace, monospace'
    ctx.fillText('[E]', size - 78, size - 36)
    ctx.globalAlpha = 1
  })
}

/**
 * Pizarra de ficha (RETOS / APRENDIZAJES): titulo pintado + 2-3 bullets
 * de tiza del CV real. E abre el panel DOM completo (la lectura de verdad
 * sigue siendo HTML). Una barra de acento pulsa cuando esta activa.
 */
export function fichaBoard(opts: {
  roomIndex: number
  kind: FichaKind
  position: readonly [number, number, number]
  rotationY?: number
  theme: RoomTheme
  locale: Locale
  /** Bullets del CV para el resumen de tiza (se truncan a ~34 chars). */
  preview: readonly string[]
  state: EngineState
  onOpen(roomIndex: number, kind: FichaKind): void
}): PropHandle {
  const id = `ficha-${opts.roomIndex}-${opts.kind}`
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // marco de madera con hull + tablero canvas
  const backing = boxMesh(2.4, 1.55, 0.06, toonMat('#5a4632'))
  backing.position.set(0, 1.62, -0.045)
  const boardTexture = chalkTexture({
    title: FICHA_TITLES[opts.kind][opts.locale],
    bullets: opts.preview,
    theme: opts.theme,
  })
  const board = new Mesh(
    new PlaneGeometry(2.2, 1.38),
    new MeshBasicMaterial({ map: boardTexture }),
  )
  board.position.set(0, 1.62, 0)
  board.userData.noOutline = true
  // barra de acento que pulsa cuando la pizarra es el interactable activo
  const pulseMat = toonMatOwn(opts.theme.accent, {
    emissive: opts.theme.accent,
    emissiveIntensity: 0.25,
  })
  const bar = boxMesh(2.4, 0.1, 0.08, pulseMat)
  bar.position.set(0, 0.78, -0.02)
  bar.userData.noOutline = true
  group.add(backing, board, bar)
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
        opts.state.activeId === id ? 0.7 + Math.sin(t * 5) * 0.3 : 0.25
    },
  }
}

// ---------------------------------------------------------------------------
// Pantallas intercambiables (PC que bootea, OFFLINE -> ONLINE, deploys)
// ---------------------------------------------------------------------------

export interface ScreenSwap {
  mesh: Mesh
  show(key: string): void
  dispose(): void
}

/**
 * Pantalla con variantes pre-renderizadas (canvas) que se intercambian
 * mutando material.map — cero draw calls extra. El dispose libera TODAS
 * las variantes (disposeDeep solo veria la activa).
 */
export function screenVariants(opts: {
  width: number
  height: number
  variants: Record<string, Omit<ScreenPanelOpts, 'width' | 'height'>>
  initial: string
}): ScreenSwap {
  const textures = new Map<string, CanvasTexture>()
  for (const [key, variant] of Object.entries(opts.variants)) {
    textures.set(
      key,
      screenTexture({ ...variant, width: opts.width, height: opts.height }),
    )
  }
  const material = new MeshBasicMaterial({
    map: textures.get(opts.initial) ?? null,
  })
  const mesh = new Mesh(new PlaneGeometry(opts.width, opts.height), material)
  mesh.userData.noOutline = true
  return {
    mesh,
    show(key) {
      const texture = textures.get(key)
      if (texture) {
        material.map = texture
      }
    },
    dispose() {
      for (const texture of textures.values()) {
        texture.dispose()
      }
      material.dispose()
    },
  }
}

/** Monitor con pantalla intercambiable (pie + marco fusionados). */
export function switchableMonitor(opts: {
  position: readonly [number, number, number]
  rotationY?: number
  width?: number
  variants: Record<string, Omit<ScreenPanelOpts, 'width' | 'height'>>
  initial: string
}): { group: Group; screen: ScreenSwap } {
  const width = opts.width ?? 0.6
  const height = width * 0.6
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
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
  const screen = screenVariants({
    width,
    height,
    variants: opts.variants,
    initial: opts.initial,
  })
  screen.mesh.position.set(0, height / 2 + 0.14, 0.01)
  group.add(body, screen.mesh)
  return { group, screen }
}

const PORTAL_LABEL = {
  es: 'Cruzar al pasado',
  en: 'Step into the past',
} as const

const EXIT_LABEL = {
  es: 'Volver al presente',
  en: 'Return to the present',
} as const

/** Textura del vortice temporal: espiral de tinta con el acento. */
function swirlTexture(accent: string): CanvasTexture {
  return makeCanvasTexture(256, (ctx, size) => {
    const c = size / 2
    const bg = ctx.createRadialGradient(c, c, 8, c, c, c)
    bg.addColorStop(0, '#1c1410')
    bg.addColorStop(0.72, '#0d0a08')
    bg.addColorStop(1, '#040302')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, size, size)
    // 3 brazos espirales (2 del acento + 1 crema) — remolino temporal
    const arms: readonly string[] = [accent, accent, '#e8d8b0']
    ctx.lineCap = 'round'
    arms.forEach((color, arm) => {
      ctx.strokeStyle = color
      ctx.globalAlpha = arm === 2 ? 0.8 : 0.9
      ctx.lineWidth = 7 - arm
      ctx.beginPath()
      const offset = (arm / arms.length) * Math.PI * 2
      for (let i = 0; i <= 60; i += 1) {
        const t = i / 60
        const angle = offset + t * Math.PI * 3.2
        const radius = 6 + t * (c - 14)
        const px = c + Math.cos(angle) * radius
        const py = c + Math.sin(angle) * radius
        if (i === 0) {
          ctx.moveTo(px, py)
        } else {
          ctx.lineTo(px, py)
        }
      }
      ctx.stroke()
    })
    ctx.globalAlpha = 1
    ctx.fillStyle = '#f2e6c8'
    ctx.beginPath()
    ctx.arc(c, c, 10, 0, Math.PI * 2)
    ctx.fill()
  })
}

interface PortalArch {
  group: Group
  update(t: number): void
}

/**
 * Arco de portal temporal: torii de madera entintada con remates del
 * acento, vortice espiral girando, motas orbitando en contrasentido,
 * letrero encima y alfombra gastada al pie. Compartido por el portal de
 * entrada (presente) y el de salida (pasado).
 */
function portalArch(accent: string, signText: string): PortalArch {
  const group = new Group()
  const arch = mergedBoxes(
    [
      { w: 0.16, h: 2.3, d: 0.16, x: -0.72, y: 1.15, z: 0 },
      { w: 0.16, h: 2.3, d: 0.16, x: 0.72, y: 1.15, z: 0 },
      { w: 2.14, h: 0.14, d: 0.24, x: 0, y: 2.38, z: 0 },
      { w: 1.66, h: 0.1, d: 0.18, x: 0, y: 2.12, z: 0 },
    ],
    toonMat('#2a1c12'),
  )
  arch.castShadow = true
  const caps = mergedBoxes(
    [
      { w: 0.24, h: 0.2, d: 0.28, x: -1.03, y: 2.38, z: 0 },
      { w: 0.24, h: 0.2, d: 0.28, x: 1.03, y: 2.38, z: 0 },
    ],
    toonMat(accent, { emissive: accent, emissiveIntensity: 0.45 }),
  )
  caps.userData.noOutline = true
  const swirl = new Mesh(
    new CircleGeometry(0.62, 32),
    new MeshBasicMaterial({ map: swirlTexture(accent) }),
  )
  swirl.position.set(0, 1.28, 0.02)
  swirl.userData.noOutline = true
  const motes = mergedBoxes(
    Array.from({ length: 9 }, (_, i) => {
      const angle = (i / 9) * Math.PI * 2
      const radius = 0.78 + (i % 3) * 0.07
      return {
        w: 0.05,
        h: 0.05,
        d: 0.05,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        z: 0,
      }
    }),
    basicMat(accent),
  )
  motes.position.set(0, 1.28, 0.08)
  motes.userData.noOutline = true
  const sign = label(signText, { size: 0.18, color: '#e8d8b0' })
  sign.position.set(0, 2.64, 0.06)
  const rug = new Mesh(unitGeo().plane, toonMat('#211812'))
  rug.rotation.x = -Math.PI / 2
  rug.scale.set(1.7, 1.1, 1)
  rug.position.set(0, 0.012, 0.55)
  rug.userData.noOutline = true
  group.add(arch, caps, swirl, motes, sign, rug)
  return {
    group,
    update: (t) => {
      swirl.rotation.z = -t * 1.3
      motes.rotation.z = t * 0.45
    },
  }
}

/** Puerta-portal al "antes" de la sala (teleporta a la sala espejo). */
export function pastPortal(opts: {
  room: RoomLayout
  position: readonly [number, number, number]
  rotationY?: number
  accent: string
  /** Año de la etapa: letrero ANTES · {año}. */
  year: string
  locale: Locale
  onEnter(roomIndex: number, spawn: { x: number; z: number }): void
}): PropHandle {
  const sign =
    opts.locale === 'es' ? `ANTES · ${opts.year}` : `BEFORE · ${opts.year}`
  const arch = portalArch(opts.accent, sign)
  arch.group.position.set(opts.position[0], opts.position[1], opts.position[2])
  arch.group.rotation.y = opts.rotationY ?? 0
  return {
    group: arch.group,
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
    update: (t) => arch.update(t),
  }
}

/** Portal de salida dentro de la mini-sala del pasado. */
export function exitPortal(opts: {
  roomIndex: number
  position: readonly [number, number, number]
  rotationY?: number
  locale: Locale
  onExit(): void
}): PropHandle {
  const sign = opts.locale === 'es' ? 'VOLVER · HOY' : 'BACK · TODAY'
  const arch = portalArch('#c8a878', sign)
  arch.group.position.set(opts.position[0], opts.position[1], opts.position[2])
  arch.group.rotation.y = opts.rotationY ?? 0
  return {
    group: arch.group,
    interactable: {
      id: `portal-exit-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2,
      label: EXIT_LABEL,
      onActivate: () => opts.onExit(),
    },
    update: (t) => arch.update(t),
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
