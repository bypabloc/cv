/**
 * @module rooms/props (engine)
 * @description Props procedurales compartidos entre salas manga-ink:
 *   escritorio, monitor (estatico e intercambiable), pizarra de ficha con
 *   titulo + tiza, GRIETA TEMPORAL al pasado (rasgadura con vortice-reloj),
 *   pedestal con el cuaderno-reseña FLOTANTE de la etapa y pila de
 *   papeles. Todo primitivas del pool toon — cero .glb, cero red.
 */
import {
  type CanvasTexture,
  CircleGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
  PointLight,
} from 'three'
import type { Box2 } from '../../lib/collision'
import { PAST_OFFSET_X, type RoomLayout } from '../../lib/layout'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { FichaKind, Interactable } from '../state'
import type { RoomTheme } from '../themes'
import {
  basicMat,
  boxMesh,
  label,
  MANGA_FONT,
  MONO_FONT,
  makeCanvasTexture,
  makeRng,
  mergedBoxes,
  outlinedMergedBoxes,
  type ScreenPanelOpts,
  screenPanel,
  screenTexture,
  toonMat,
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

/** Silla simple contorneada: asiento + respaldo (local -Z) + 2 patas. */
export function chair(opts: {
  position: readonly [number, number, number]
  rotationY?: number
  color?: string
}): Group {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.42, h: 0.05, d: 0.42, x: 0, y: 0.44, z: 0 },
        { w: 0.42, h: 0.5, d: 0.05, x: 0, y: 0.72, z: -0.2 },
        { w: 0.05, h: 0.44, d: 0.05, x: -0.17, y: 0.22, z: -0.1 },
        { w: 0.05, h: 0.44, d: 0.05, x: 0.17, y: 0.22, z: -0.1 },
      ],
      toonMat(opts.color ?? '#4a3b2a'),
      { inflate: 0.03 },
    ),
  )
  return group
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
  // pie + marco + teclado fusionados (1 draw call)
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
      { w: 0.36, h: 0.025, d: 0.14, x: 0, y: 0.013, z: 0.26 },
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
 * sigue siendo HTML). El marco toma el `trim` del theme (guiño morado en
 * el aula); sin barra inferior (el feedback vive en el prompt del HUD).
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
  onOpen(roomIndex: number, kind: FichaKind): void
}): PropHandle {
  const id = `ficha-${opts.roomIndex}-${opts.kind}`
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // marco (trim del theme) con hull + tablero canvas
  const backing = boxMesh(
    2.4,
    1.55,
    0.06,
    toonMat(opts.theme.trim ?? '#5a4632'),
  )
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
  group.add(backing, board)
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
      { w: 0.36, h: 0.025, d: 0.14, x: 0, y: 0.013, z: 0.26 },
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

/**
 * Vortice-RELOJ del portal: espiral de tinta + 12 marcas horarias y los
 * numeros 12/3/6/9 distorsionados cayendo hacia el centro. El mesh entero
 * rota (la "espiral de un reloj" que pidio el diseño).
 */
function clockSwirlTexture(accent: string): CanvasTexture {
  return makeCanvasTexture(256, (ctx, size) => {
    const c = size / 2
    const bg = ctx.createRadialGradient(c, c, 8, c, c, c)
    bg.addColorStop(0, '#1c1622')
    bg.addColorStop(0.72, '#0d0a10')
    bg.addColorStop(1, '#040305')
    ctx.fillStyle = bg
    ctx.beginPath()
    ctx.arc(c, c, c, 0, Math.PI * 2)
    ctx.fill()
    // 3 brazos espirales (2 del acento + 1 crema) — remolino temporal
    const arms: readonly string[] = [accent, accent, '#e8d8b0']
    ctx.lineCap = 'round'
    arms.forEach((color, arm) => {
      ctx.strokeStyle = color
      ctx.globalAlpha = arm === 2 ? 0.8 : 0.9
      ctx.lineWidth = 6 - arm
      ctx.beginPath()
      const offset = (arm / arms.length) * Math.PI * 2
      for (let i = 0; i <= 60; i += 1) {
        const t = i / 60
        const angle = offset + t * Math.PI * 3.2
        const radius = 6 + t * (c - 18)
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
    // marcas horarias en el borde (esfera de reloj)
    ctx.globalAlpha = 0.85
    ctx.strokeStyle = '#e8d8b0'
    ctx.lineWidth = 3
    for (let i = 0; i < 12; i += 1) {
      const angle = (i / 12) * Math.PI * 2
      const r0 = c - 5
      const r1 = i % 3 === 0 ? c - 20 : c - 12
      ctx.beginPath()
      ctx.moveTo(c + Math.cos(angle) * r0, c + Math.sin(angle) * r0)
      ctx.lineTo(c + Math.cos(angle) * r1, c + Math.sin(angle) * r1)
      ctx.stroke()
    }
    // numeros 12/3/6/9 estirados en espiral (los "traga" el vortice)
    ctx.fillStyle = '#f2e6c8'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const numbers: readonly (readonly [string, number])[] = [
      ['12', -Math.PI / 2],
      ['3', 0],
      ['6', Math.PI / 2],
      ['9', Math.PI],
    ]
    for (const [text, angle] of numbers) {
      const r = c * 0.62
      ctx.save()
      ctx.translate(c + Math.cos(angle) * r, c + Math.sin(angle) * r)
      ctx.rotate(angle + Math.PI / 2 + 0.5)
      ctx.transform(1, 0.22, -0.3, 0.9, 0, 0)
      ctx.font = `bold 34px ${MANGA_FONT}`
      ctx.globalAlpha = 0.92
      ctx.fillText(text, 0, 0)
      ctx.restore()
    }
    // nucleo
    ctx.globalAlpha = 1
    ctx.fillStyle = '#f2e6c8'
    ctx.beginPath()
    ctx.arc(c, c, 8, 0, Math.PI * 2)
    ctx.fill()
  })
}

/** Silueta irregular de la grieta (rasgadura — NUNCA forma de puerta). */
function riftOutline(
  size: number,
  rng: () => number,
): readonly (readonly [number, number])[] {
  const cx = size / 2
  const cy = size / 2
  const rx = size * 0.3
  const ry = size * 0.43
  const spikes = 16
  return Array.from({ length: spikes }, (_, i) => {
    const angle = (i / spikes) * Math.PI * 2
    const jag = 0.66 + rng() * 0.5
    return [
      cx + Math.cos(angle) * rx * jag,
      cy + Math.sin(angle) * ry * jag,
    ] as const
  })
}

function traceRift(
  ctx: CanvasRenderingContext2D,
  points: readonly (readonly [number, number])[],
): void {
  ctx.beginPath()
  points.forEach(([x, y], i) => {
    if (i === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.closePath()
}

/**
 * Textura de la grieta temporal: rasgadura oscura de bordes irregulares
 * con glow del acento, filo crema y fisuras ramificandose hacia el muro.
 * Fondo transparente (se pega plana al muro, sin marco).
 */
function riftTexture(accent: string): CanvasTexture {
  let seed = 13
  for (const ch of accent) {
    seed = seed * 31 + ch.charCodeAt(0)
  }
  const rng = makeRng(seed >>> 0)
  return makeCanvasTexture(512, (ctx, size) => {
    ctx.clearRect(0, 0, size, size)
    const points = riftOutline(size, rng)
    // vacio interior
    traceRift(ctx, points)
    const bg = ctx.createRadialGradient(
      size / 2,
      size / 2,
      10,
      size / 2,
      size / 2,
      size * 0.45,
    )
    bg.addColorStop(0, '#050308')
    bg.addColorStop(1, '#130c1a')
    ctx.fillStyle = bg
    ctx.fill()
    // borde: glow del acento + trazo firme + filo crema
    ctx.lineJoin = 'round'
    traceRift(ctx, points)
    ctx.strokeStyle = accent
    ctx.globalAlpha = 0.35
    ctx.lineWidth = 16
    ctx.stroke()
    traceRift(ctx, points)
    ctx.globalAlpha = 0.95
    ctx.lineWidth = 5
    ctx.stroke()
    traceRift(ctx, points)
    ctx.strokeStyle = '#f2e6c8'
    ctx.globalAlpha = 0.85
    ctx.lineWidth = 2
    ctx.stroke()
    // fisuras/destellos ramificandose desde el borde hacia afuera
    ctx.strokeStyle = accent
    ctx.lineCap = 'round'
    for (let i = 0; i < 7; i += 1) {
      const point = points[Math.floor(rng() * points.length)]
      if (!point) {
        continue
      }
      let [x, y] = point
      const away = Math.atan2(y - size / 2, x - size / 2)
      ctx.globalAlpha = 0.75
      ctx.lineWidth = 2.5
      ctx.beginPath()
      ctx.moveTo(x, y)
      for (let s = 0; s < 3; s += 1) {
        x += Math.cos(away + (rng() - 0.5) * 1.1) * (10 + rng() * 16)
        y += Math.sin(away + (rng() - 0.5) * 1.1) * (10 + rng() * 16)
        ctx.lineTo(x, y)
      }
      ctx.stroke()
    }
    ctx.globalAlpha = 1
  })
}

interface PortalRift {
  group: Group
  update(t: number): void
}

/**
 * GRIETA TEMPORAL (rediseño 2026-07-04, decision del usuario): rasgadura
 * irregular pegada plana al muro — SIN marco de puerta ni arco — con el
 * vortice-reloj girando adentro, motas orbitando en contrasentido, letrero
 * y marca oscura en el piso. ~2.9 m de alto. Compartida por el portal de
 * entrada (presente) y el de salida (pasado).
 */
function timeRift(accent: string, signText: string): PortalRift {
  const group = new Group()
  const rift = new Mesh(
    new PlaneGeometry(2.7, 3),
    new MeshBasicMaterial({ map: riftTexture(accent), transparent: true }),
  )
  rift.position.set(0, 1.5, 0.04)
  rift.userData.noOutline = true
  const swirl = new Mesh(
    new CircleGeometry(0.8, 40),
    new MeshBasicMaterial({ map: clockSwirlTexture(accent) }),
  )
  swirl.position.set(0, 1.5, 0.055)
  swirl.userData.noOutline = true
  const motes = mergedBoxes(
    Array.from({ length: 12 }, (_, i) => {
      const angle = (i / 12) * Math.PI * 2
      const radius = 0.92 + (i % 3) * 0.09
      return {
        w: 0.045,
        h: 0.045,
        d: 0.045,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        z: 0,
      }
    }),
    basicMat(accent),
  )
  motes.position.set(0, 1.5, 0.07)
  motes.userData.noOutline = true
  const sign = label(signText, { size: 0.16, color: '#e8d8b0' })
  sign.position.set(0, 2.88, 0.09)
  const scorch = new Mesh(unitGeo().plane, toonMat('#15101c'))
  scorch.rotation.x = -Math.PI / 2
  scorch.scale.set(2.1, 1.3, 1)
  scorch.position.set(0, 0.014, 0.5)
  scorch.userData.noOutline = true
  group.add(rift, swirl, motes, sign, scorch)
  return {
    group,
    update: (t) => {
      // la espiral del reloj gira "hacia atras" y la grieta respira apenas
      swirl.rotation.z = -t * 1.15
      motes.rotation.z = t * 0.5
      const pulse = 1 + Math.sin(t * 2.1) * 0.015
      rift.scale.set(pulse, pulse, 1)
    },
  }
}

/** Grieta-portal al "antes" de la sala (teleporta a la sala espejo).
 *  SIEMPRE en el muro que queda a la MANO IZQUIERDA del jugador que
 *  avanza hacia la siguiente sala — el muro +X: mirando +Z, la derecha
 *  es -X (decision del usuario 2026-07-04; antes estaba espejado en -X,
 *  que en primera persona es la derecha). */
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
  const rift = timeRift(opts.accent, sign)
  rift.group.position.set(opts.position[0], opts.position[1], opts.position[2])
  rift.group.rotation.y = opts.rotationY ?? 0
  return {
    group: rift.group,
    interactable: {
      id: `portal-${opts.room.index}`,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2.2,
      label: PORTAL_LABEL,
      onActivate: () =>
        opts.onEnter(opts.room.index, {
          x: PAST_OFFSET_X,
          z: opts.room.z + 1.6,
        }),
    },
    update: (t) => {
      rift.update(t)
      // hum grave del vortice, audible al acercarse (keep-alive)
      sfx.feed(
        `portal-${opts.room.index}`,
        'portal',
        opts.position[0],
        opts.position[2],
      )
    },
  }
}

/** Grieta de salida dentro de la mini-sala del pasado. */
export function exitPortal(opts: {
  roomIndex: number
  position: readonly [number, number, number]
  rotationY?: number
  locale: Locale
  onExit(): void
}): PropHandle {
  const sign = opts.locale === 'es' ? 'VOLVER · HOY' : 'BACK · TODAY'
  const rift = timeRift('#c8a878', sign)
  rift.group.position.set(opts.position[0], opts.position[1], opts.position[2])
  rift.group.rotation.y = opts.rotationY ?? 0
  return {
    group: rift.group,
    interactable: {
      id: `portal-exit-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2.2,
      label: EXIT_LABEL,
      onActivate: () => opts.onExit(),
    },
    update: (t) => {
      rift.update(t)
      sfx.feed(
        `portal-exit-${opts.roomIndex}`,
        'portal',
        opts.position[0],
        opts.position[2],
      )
    },
  }
}

const NOTE_LABEL = {
  es: 'Leer la reseña de la etapa',
  en: 'Read the stage overview',
} as const

/** Pagina abierta del cuaderno: papel con margen + renglones + resumen. */
function notebookTexture(opts: {
  title: string
  lines: readonly string[]
}): CanvasTexture {
  return makeCanvasTexture(256, (ctx, size) => {
    ctx.fillStyle = '#f2ecd9'
    ctx.fillRect(0, 0, size, size)
    // margen de cuaderno + renglones tenues
    ctx.strokeStyle = 'rgba(160,80,80,0.55)'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(34, 8)
    ctx.lineTo(34, size - 8)
    ctx.stroke()
    ctx.strokeStyle = 'rgba(90,90,140,0.22)'
    for (let y = 64; y < size - 12; y += 30) {
      ctx.beginPath()
      ctx.moveTo(10, y)
      ctx.lineTo(size - 10, y)
      ctx.stroke()
    }
    ctx.fillStyle = '#241a2e'
    ctx.font = `bold 24px ${MANGA_FONT}`
    ctx.fillText(opts.title.slice(0, 17), 44, 40)
    ctx.font = `19px ${MONO_FONT}`
    let y = 88
    for (const line of opts.lines.slice(0, 5)) {
      ctx.fillText(line.slice(0, 19), 44, y)
      y += 30
    }
    ctx.globalAlpha = 0.55
    ctx.font = `17px ${MONO_FONT}`
    ctx.fillText('[E]', size - 52, size - 16)
    ctx.globalAlpha = 1
  })
}

/** Altura base del cuaderno flotante sobre su pedestal. */
const NOTE_FLOAT_Y = 1.42

/**
 * Pedestal con el cuaderno de la etapa FLOTANDO encima (a la mano
 * DERECHA del jugador que avanza — muro -X — junto a la puerta de
 * salida, el espejo de la grieta-al-pasado del muro izquierdo). El
 * cuaderno levita separado del pilar con vaiven + halo del acento +
 * luz propia (tier full): llama la atencion como la grieta. Mismo
 * lenguaje visual que el pedestal de contacto de la CIMA. El resumen
 * corto se lee en la pagina 3D y E abre el panel DOM con la reseña.
 */
export function lecternNotebook(opts: {
  roomIndex: number
  position: readonly [number, number, number]
  rotationY?: number
  theme: RoomTheme
  /** Titulo + lineas cortas del cuaderno 3D (se truncan a ~19 chars). */
  notebook: { title: string; lines: readonly string[] }
  /** Reseña completa para el panel DOM (titulo + parrafos). */
  story: { title: string; paragraphs: readonly string[] }
  /** Luz puntual de acento sobre el cuaderno (solo tier full). */
  withLight?: boolean
  onOpen(title: string, paragraphs: readonly string[]): void
}): PropHandle {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  const trim = opts.theme.trim ?? opts.theme.accent
  const units = unitGeo()
  // pilar cilindrico (mismo lenguaje que el pedestal de contacto)
  const pedestal = new Mesh(units.cylinder, toonMat('#141a26'))
  pedestal.scale.set(0.5, 0.9, 0.5)
  pedestal.position.y = 0.45
  pedestal.castShadow = true
  // filo superior con el trim de la sala (guiño)
  const lip = new Mesh(
    units.cylinder,
    toonMat(trim, { emissive: trim, emissiveIntensity: 0.35 }),
  )
  lip.scale.set(0.54, 0.04, 0.54)
  lip.position.y = 0.92
  lip.userData.noOutline = true
  group.add(pedestal, lip)
  // cuaderno FLOTANDO separado del pilar: pagina vertical hacia la sala
  // + halo del acento detras (el pulso lo anima el update)
  const float = new Group()
  const page = new Mesh(
    new PlaneGeometry(0.62, 0.5),
    new MeshBasicMaterial({ map: notebookTexture(opts.notebook) }),
  )
  page.userData.noOutline = true
  const haloMat = new MeshBasicMaterial({
    color: trim,
    transparent: true,
    opacity: 0.26,
  })
  const halo = new Mesh(new PlaneGeometry(0.76, 0.62), haloMat)
  halo.position.z = -0.02
  halo.userData.noOutline = true
  float.add(halo, page)
  float.position.set(0, NOTE_FLOAT_Y, 0.02)
  float.rotation.x = -0.1
  group.add(float)
  const light = opts.withLight ? new PointLight(trim, 1.5, 3.5) : null
  if (light) {
    light.position.set(0, NOTE_FLOAT_Y + 0.35, 0.4)
    group.add(light)
  }
  return {
    group,
    interactable: {
      id: `nota-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2.2,
      label: NOTE_LABEL,
      onActivate: () => opts.onOpen(opts.story.title, opts.story.paragraphs),
    },
    update: (t) => {
      // levita: vaiven vertical + balanceo suave + halo/luz latiendo
      float.position.y = NOTE_FLOAT_Y + Math.sin(t * 1.7) * 0.06
      float.rotation.y = Math.sin(t * 0.8) * 0.16
      const pulse = (Math.sin(t * 2.3) + 1) / 2
      haloMat.opacity = 0.2 + pulse * 0.14
      if (light) {
        light.intensity = 1.2 + pulse * 0.7
      }
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
