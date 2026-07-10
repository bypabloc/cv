/**
 * @module rooms/props (engine)
 * @description Props procedurales compartidos entre salas manga-ink:
 *   escritorio, monitor (estatico e intercambiable), pizarra de ficha con
 *   titulo + tiza, FRACTURA DIMENSIONAL (todos los portales: rasgadura
 *   shader con aberracion RGB local),
 *   pedestal con el cuaderno-reseña FLOTANTE de la etapa, pila de papeles
 *   y los 4 helpers del CANON de sala (plan journey-salas-estandar):
 *   officeLayout, npcCoworkers, wallArt y softwareShowcase. Todo
 *   primitivas del pool toon — cero .glb, cero red.
 */
import {
  BoxGeometry,
  CanvasTexture,
  Color,
  Group,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
  PointLight,
  ShaderMaterial,
  SRGBColorSpace,
} from 'three'
import type { Box2 } from '../../lib/collision'
import { PAST_OFFSET_X, type RoomLayout } from '../../lib/layout'
import type { Locale, RoomTexts } from '../../lib/rooms'
import { sfx } from '../audio'
import { type CharacterSpec, makeNpc, type NpcHandle } from '../character'
import {
  type NpcDialog,
  type NpcTalk,
  npcTalk,
  type OpenDialog,
} from '../dialog'
import type {
  EngineState,
  FichaKind,
  Interactable,
  ShowcaseRef,
  ShowcaseView,
} from '../state'
import type { RoomTheme } from '../themes'
import {
  type BoxSpec,
  boxMesh,
  type DrawFn,
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
import { placeFurniture } from './furniture'

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

/**
 * Teclado de escritorio: placa negra con las teclas horneadas en una textura
 * Canvas (una cuadricula de teclas + barra espaciadora). Se apoya en la mesa
 * mirando +Z (el que teclea esta detras, en -Z). 2 draw calls (base + placa
 * de teclas). Lo usa el aula para que las PCs "tengan teclado" de verdad.
 */
export function deskKeyboard(opts: {
  position: readonly [number, number, number]
  rotationY?: number
  width?: number
}): Group {
  const width = opts.width ?? 0.34
  const depth = width * 0.42
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // base ligeramente inclinada (parte trasera mas alta)
  const base = new Mesh(new BoxGeometry(width, 0.02, depth), toonMat('#26262c'))
  base.rotation.x = -0.14
  base.castShadow = true
  base.userData.noOutline = true
  // teclas horneadas: cuadricula de rectangulos claros + barra espaciadora
  const tex = makeCanvasTexture(128, (ctx, size) => {
    ctx.fillStyle = '#1c1c22'
    ctx.fillRect(0, 0, size, size)
    ctx.fillStyle = '#c9c9cf'
    const cols = 12
    const rows = 4
    const pad = 8
    const gap = 3
    const kw = (size - pad * 2 - gap * (cols - 1)) / cols
    const kh = ((size - pad * 2) * 0.62 - gap * (rows - 1)) / rows
    for (let r = 0; r < rows; r += 1) {
      const off = r * 3 // filas escalonadas
      for (let c = 0; c < cols; c += 1) {
        const x = pad + off + c * (kw + gap)
        const y = pad + r * (kh + gap)
        if (x + kw > size - pad) {
          continue
        }
        ctx.fillRect(x, y, kw, kh)
      }
    }
    // barra espaciadora
    ctx.fillRect(size * 0.28, size - pad - kh, size * 0.44, kh)
  })
  const keys = new Mesh(
    new PlaneGeometry(width - 0.02, depth - 0.01),
    new MeshBasicMaterial({ map: tex }),
  )
  keys.rotation.x = -Math.PI / 2 - 0.14
  keys.position.set(0, 0.012, 0)
  keys.userData.noOutline = true
  group.add(base, keys)
  return group
}

/**
 * Mouse de escritorio: media esfera achatada (cuerpo) + una ranura de botones
 * horneada por escala. Se apoya en la mesa; se coloca al costado del teclado.
 * 1 draw call (la esfera compartida de unitGeo escalada). Lo usa el aula junto
 * al deskKeyboard.
 */
export function deskMouse(opts: {
  position: readonly [number, number, number]
  color?: string
}): Group {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  // cuerpo: esfera unidad escalada a un ovalo BAJO y ALARGADO (ancho 0.055,
  // largo 0.11, alto 0.035) para que parezca un mouse, no un boton. Color del
  // teclado (negro `#26262c`) por defecto para que CONTRASTE con la mesa blanca
  // y se vea (pedido de Pablo: mismo color que la PC/teclado). Se sube y para
  // apoyar sobre la mesa.
  const body = new Mesh(unitGeo().sphere, toonMat(opts.color ?? '#26262c'))
  body.scale.set(0.055, 0.035, 0.11)
  body.position.y = 0.014
  body.castShadow = true
  // ranura de botones: una linea gris CLARA al frente (division izq/der) que
  // contrasta con el cuerpo negro.
  const split = new Mesh(
    new BoxGeometry(0.002, 0.001, 0.05),
    toonMat('#c9c9cf'),
  )
  split.position.set(0, 0.032, 0.028)
  split.userData.noOutline = true
  group.add(body, split)
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

/**
 * Estilo de las pizarras RETOS/APRENDIZAJES por tipo de sala:
 * - `chalk`: pizarra verde de aula con tiza y marco de madera.
 * - `whiteboard`: pizarra blanca de oficina con marcador negro (DEFAULT).
 * - `glass`: pizarra de cristal esmerilado (el estilo "nuevo" del futuro).
 */
export type BoardStyle = 'chalk' | 'whiteboard' | 'glass'

interface BoardPalette {
  /** Fondo del tablero; null = cristal esmerilado (se pinta con alpha). */
  bg: string | null
  /** Texto (titulo + bullets). */
  ink: string
  /** Trazo del marco interno. */
  border: string
  /** Color del backing (marco fisico). */
  frame: string
  /** El tablero se renderiza translucido (cristal). */
  transparent: boolean
}

const BOARD_PALETTES: Record<BoardStyle, BoardPalette> = {
  chalk: {
    bg: '#33503f',
    ink: '#eef2e6',
    border: '#e8e4d4',
    frame: '#7a5230',
    transparent: false,
  },
  whiteboard: {
    bg: '#f5f5f1',
    ink: '#1a1c22',
    border: '#c9ccd2',
    frame: '#b0b4bc',
    transparent: false,
  },
  glass: {
    bg: null,
    ink: '#243044',
    border: '#cdd8ea',
    frame: '#c6ccd6',
    transparent: true,
  },
}

/** Titulo + subrayado de acento + bullets del CV, segun el estilo de sala. */
function boardTexture(
  style: BoardStyle,
  opts: { title: string; bullets: readonly string[]; theme: RoomTheme },
): CanvasTexture {
  const pal = BOARD_PALETTES[style]
  const rng = makeRng(opts.title.length * 31 + opts.bullets.length)
  return makeCanvasTexture(512, (ctx, size) => {
    if (pal.bg) {
      ctx.fillStyle = pal.bg
      ctx.fillRect(0, 0, size, size)
    } else {
      // cristal esmerilado: base blanca translucida + reflejo diagonal
      ctx.clearRect(0, 0, size, size)
      ctx.fillStyle = 'rgba(226,236,248,0.42)'
      ctx.fillRect(0, 0, size, size)
      ctx.fillStyle = 'rgba(255,255,255,0.16)'
      ctx.beginPath()
      ctx.moveTo(0, size * 0.22)
      ctx.lineTo(size * 0.5, 0)
      ctx.lineTo(size * 0.82, 0)
      ctx.lineTo(0, size * 0.62)
      ctx.closePath()
      ctx.fill()
    }
    // marco interno
    ctx.strokeStyle = pal.border
    ctx.lineCap = 'round'
    ctx.globalAlpha = style === 'chalk' ? 0.5 : 0.7
    ctx.lineWidth = 4
    ctx.strokeRect(12, 12, size - 24, size - 24)
    ctx.globalAlpha = 1
    // titulo + subrayado con el acento de la sala
    ctx.fillStyle = pal.ink
    ctx.font = 'bold 58px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(opts.title, 36, 96)
    ctx.strokeStyle = opts.theme.accent
    ctx.lineWidth = 6
    ctx.beginPath()
    ctx.moveTo(36, 118)
    // trazo irregular solo en tiza; recto en marcador/cristal
    const jitter = style === 'chalk' ? rng() * 3 : 0
    ctx.lineTo(36 + Math.min(420, opts.title.length * 34), 118 + jitter)
    ctx.stroke()
    // bullets cortos (el detalle completo vive en el panel DOM con E)
    ctx.fillStyle = pal.ink
    ctx.font = '26px "Space Grotesk", system-ui, sans-serif'
    let y = 190
    for (const bullet of opts.bullets.slice(0, 3)) {
      const text = bullet.length > 34 ? `${bullet.slice(0, 33)}…` : bullet
      ctx.fillText(`· ${text}`, 36, y)
      y += 88
    }
    // hint de interaccion
    ctx.globalAlpha = 0.55
    ctx.font = '22px "Space Mono", ui-monospace, monospace'
    ctx.fillText('[E]', size - 78, size - 36)
    ctx.globalAlpha = 1
  })
}

/**
 * Pizarra de ficha (RETOS / APRENDIZAJES): titulo + 2-3 bullets del CV real.
 * E abre el panel DOM completo (la lectura de verdad sigue siendo HTML). El
 * `boardStyle` define el look segun el tipo de sala (chalk aula / whiteboard
 * oficinas / glass futuro); el marco fisico toma su color de la paleta.
 */
export function fichaBoard(opts: {
  roomIndex: number
  kind: FichaKind
  position: readonly [number, number, number]
  rotationY?: number
  theme: RoomTheme
  locale: Locale
  /** Bullets del CV para el resumen (se truncan a ~34 chars). */
  preview: readonly string[]
  /** Estilo de pizarra por tipo de sala (default whiteboard). */
  boardStyle?: BoardStyle
  onOpen(roomIndex: number, kind: FichaKind): void
}): PropHandle {
  const id = `ficha-${opts.roomIndex}-${opts.kind}`
  const style = opts.boardStyle ?? 'whiteboard'
  const pal = BOARD_PALETTES[style]
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // marco fisico segun el estilo (madera / aluminio / metalico)
  const backing = boxMesh(2.4, 1.55, 0.06, toonMat(pal.frame))
  backing.position.set(0, 1.62, -0.045)
  const boardTex = boardTexture(style, {
    title: FICHA_TITLES[opts.kind][opts.locale],
    bullets: opts.preview,
    theme: opts.theme,
  })
  const board = new Mesh(
    new PlaneGeometry(2.2, 1.38),
    new MeshBasicMaterial({ map: boardTex, transparent: pal.transparent }),
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
  /** Color del cuerpo (default oscuro `#15151a`; crema para CRT viejo). */
  bodyColor?: string
  /** Cuerpo CRT abultado (monitor blanco de los 2000) en vez del plano. */
  crt?: boolean
}): { group: Group; screen: ScreenSwap } {
  const width = opts.width ?? 0.6
  const height = width * 0.6
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  const screenY = height / 2 + 0.14
  // CRT viejo: bisel grueso + tubo trasero abultado + base + teclado.
  // Plano: marco fino (flat-screen). El screenZ apoya la pantalla en la cara
  // frontal del bisel/marco.
  const crtParts: BoxSpec[] = [
    { w: 0.2, h: 0.06, d: 0.2, x: 0, y: 0.03, z: -0.02 },
    { w: 0.1, h: 0.08, d: 0.1, x: 0, y: 0.1, z: -0.02 },
    { w: width + 0.14, h: height + 0.14, d: 0.16, x: 0, y: screenY, z: 0 },
    { w: width - 0.04, h: height - 0.04, d: 0.16, x: 0, y: screenY, z: -0.15 },
    { w: 0.42, h: 0.03, d: 0.16, x: 0, y: 0.015, z: 0.3 },
  ]
  const flatParts: BoxSpec[] = [
    { w: 0.16, h: 0.14, d: 0.16, x: 0, y: 0.07, z: 0 },
    { w: width + 0.05, h: height + 0.05, d: 0.05, x: 0, y: screenY, z: -0.02 },
    { w: 0.36, h: 0.025, d: 0.14, x: 0, y: 0.013, z: 0.26 },
  ]
  const body = mergedBoxes(
    opts.crt ? crtParts : flatParts,
    toonMat(opts.bodyColor ?? '#15151a'),
  )
  body.userData.noOutline = true
  const screen = screenVariants({
    width,
    height,
    variants: opts.variants,
    initial: opts.initial,
  })
  screen.mesh.position.set(0, screenY, opts.crt ? 0.082 : 0.01)
  group.add(body, screen.mesh)
  return { group, screen }
}

/**
 * Silla escolar simple de 4 patas (asiento + respaldo + 4 patas), fusionada
 * en 1 mesh (1 draw call). El respaldo queda en el lado -Z local: colocada con
 * rotationY 0, el que se sienta mira +Z. Para el aula 2011 (bajos recursos):
 * NO es la silla de oficina con base/ruedas del pack.
 */
export function schoolChair(opts: {
  position: readonly [number, number, number]
  rotationY?: number
  color?: string
}): Group {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  const seatY = 0.46
  const legH = seatY - 0.03
  const spread = 0.19 // media distancia entre patas
  const mesh = mergedBoxes(
    [
      { w: 0.44, h: 0.04, d: 0.42, x: 0, y: seatY, z: 0 }, // asiento
      { w: 0.44, h: 0.44, d: 0.04, x: 0, y: seatY + 0.24, z: -0.19 }, // respaldo
      { w: 0.04, h: legH, d: 0.04, x: -spread, y: legH / 2, z: -spread }, // patas
      { w: 0.04, h: legH, d: 0.04, x: spread, y: legH / 2, z: -spread },
      { w: 0.04, h: legH, d: 0.04, x: -spread, y: legH / 2, z: spread },
      { w: 0.04, h: legH, d: 0.04, x: spread, y: legH / 2, z: spread },
    ],
    toonMat(opts.color ?? '#a9743f'),
  )
  mesh.castShadow = true
  group.add(mesh)
  return group
}

const PORTAL_LABEL = {
  es: 'Cruzar al pasado',
  en: 'Step into the past',
} as const

const EXIT_LABEL = {
  es: 'Volver al presente',
  en: 'Return to the present',
} as const

// ---------------------------------------------------------------------------
// FRACTURA DIMENSIONAL (rediseño 2026-07-10, iterado con el dueno: SIN
// glitch — todo movimiento continuo y fluido; 2da iteracion: sin esquirlas
// poligonales sueltas, "se leian como triangulos random" sin proposito
// claro — eliminadas): dos formas segun el destino. PASADO/SALIDA = GRIETA
// ROTA (fisura vertical que serpentea, con ramas, filo caliente y rayos de
// energia brotando — una ruptura del muro, nunca una puerta). FUTURO/
// REGRESO = WORMHOLE tipo puente Einstein-Rosen (disco de streaks
// radiales difuminados torciendose hacia el centro con lente
// gravitacional + anillo de fotones: absorbe el espacio-tiempo). Ambos
// viven en el shader del MESH (cero postfx fullscreen, canon toon limpio
// intacto). 1-2 draw calls por portal: fractura + letrero/año opcional.
// ---------------------------------------------------------------------------

/** Paleta + forma por tipo de portal. Semantica (re-decidido por el dueno
 *  2026-07-10, segunda iteracion): los wormholes (future/return) vuelven a
 *  una paleta azul-blanco-gris (reemplaza el magenta/cian anterior) — el
 *  sentido se sigue distinguiendo por el TONO de azul (ida = azul electrico
 *  profundo, regreso = azul-gris mas frio/desaturado) y por el nucleo
 *  blanco compartido. El año sigue visible. La grieta al pasado NO cambia
 *  (ambar/sepia, le gusta al dueno). */
const TEAR_STYLES = {
  /** Ida a la sala siguiente: wormhole azul electrico, nucleo blanco. */
  future: { core: '#eaf3ff', edge: '#1f6fe0', fringe: 1, shape: 'wormhole' },
  /** Regreso a la sala anterior: wormhole azul-gris frio, nucleo blanco. */
  return: { core: '#eef2f6', edge: '#5c7a94', fringe: 1, shape: 'wormhole' },
  /** Grieta al pasado: fisura rota ambar sobre sepia. */
  past: { core: '#ffb454', edge: '#8a5a2a', fringe: 0.5, shape: 'crack' },
  /** Salida del pasado: fisura ambar con filo cian (el presente llama). */
  exit: { core: '#ffb454', edge: '#2ae0ff', fringe: 0.7, shape: 'crack' },
} as const

type TearKind = keyof typeof TEAR_STYLES

const TEAR_VERT = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

// GRIETA ROTA (pasado/salida): fisura vertical que serpentea (meandro suave
// + quiebres finos), afilada en ambas puntas, con 3 ramas diagonales y
// fisuras capilares — una RUPTURA dimensional del muro, nunca una puerta.
// Interior de vacio profundo con brasas que derivan; filo caliente que
// respira, y RAYOS DE ENERGIA brotando del filo hacia afuera (arcos que
// titilan y se extinguen en loop, como electricidad escapando de la
// ruptura). Todo continuo y fluido: CERO glitch, cero saltos. 1 draw call.
const CRACK_FRAG = `
  uniform float uTime;
  uniform vec3 uCore;
  uniform vec3 uEdge;
  uniform float uSeed;
  uniform float uAspect;
  uniform float uFringe;
  varying vec2 vUv;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453);
  }
  float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  // distancia a un rayo quebrado (zigzag) que nace en 'a' hacia 'dirB':
  // cada segmento se desvia con ruido, como un arco electrico real.
  float boltDist(vec2 p, vec2 a, vec2 dirB, float len, float t) {
    vec2 dir = normalize(dirB);
    vec2 perp = vec2(-dir.y, dir.x);
    float h = clamp(dot(p - a, dir) / len, 0.0, 1.0);
    float wobble = (vnoise(vec2(h * 9.0 + t * 3.1, t)) - 0.5) * 0.14
      * smoothstep(0.0, 0.15, h) * smoothstep(1.0, 0.7, h);
    vec2 spine = a + dir * h * len + perp * wobble;
    return length(p - spine);
  }

  // distancia a una rama recta que nace en 'a' hacia 'dirB', afilandose
  float branchDist(vec2 p, vec2 a, vec2 dirB, float len, float w0) {
    vec2 pa = p - a;
    float h = clamp(dot(pa, dirB) / len, 0.0, 1.0);
    float d = length(pa - dirB * h * len);
    return d - w0 * (1.0 - h);
  }

  void main() {
    vec2 p = (vUv - 0.5) * vec2(2.0 * uAspect, 2.0);

    // tronco de la grieta: linea vertical que serpentea, afilada en puntas
    float meander = (vnoise(vec2(p.y * 1.6 + uSeed, uSeed)) - 0.5) * 0.5;
    float jag = (vnoise(vec2(p.y * 6.5 + uSeed * 2.7, uSeed + 4.0)) - 0.5)
      * 0.24;
    float cx = meander + jag;
    float taper = 1.0 - smoothstep(0.35, 0.96, abs(p.y));
    float wVar = 0.45 + vnoise(vec2(p.y * 3.1 + uSeed, uSeed + 9.0)) * 0.9;
    float w = 0.13 * taper * wVar;
    float d = abs(p.x - cx) - w;

    // 3 ramas diagonales (sub-grietas que nacen del tronco)
    float side = step(0.5, hash(vec2(uSeed, 1.0))) * 2.0 - 1.0;
    d = min(d, branchDist(
      p, vec2(cx, 0.28), normalize(vec2(0.75 * side, 0.55)), 0.42, 0.05));
    d = min(d, branchDist(
      p, vec2(cx, -0.2), normalize(vec2(-0.8 * side, -0.45)), 0.4, 0.045));
    d = min(d, branchDist(
      p, vec2(cx, 0.02), normalize(vec2(-0.7 * side, 0.2)), 0.34, 0.04));

    if (d > 0.5) {
      discard;
    }

    // respiracion suave del filo (continua, sin saltos)
    float breathe = 0.5 + 0.5 * sin(uTime * 1.3 + uSeed);

    // mascaras: interior + filo + fringes suaves del duotono
    float ab = 0.02 * uFringe;
    float inside = smoothstep(0.015, -0.015, d);
    float eG = smoothstep(0.075, 0.0, abs(d));
    float eR = smoothstep(0.06, 0.0, abs(d + ab));
    float eB = smoothstep(0.06, 0.0, abs(d - ab));

    // interior: vacio profundo con brasas que derivan lento
    float ember = vnoise(p * 3.0 + vec2(uSeed, uTime * 0.12));
    vec3 col = mix(vec3(0.02, 0.012, 0.008), uCore * 0.35, ember * ember);
    col *= inside;

    // filo caliente + fringes
    col += mix(uCore, vec3(1.0), 0.35) * eG * (0.85 + 0.3 * breathe);
    col += uCore * eR * 0.5 * uFringe;
    col += uEdge * eB * 0.6;

    // resplandor que sangra hacia el muro (la ruptura ilumina)
    float halo = smoothstep(0.34, 0.0, d) * (1.0 - inside);
    col += uCore * halo * (0.16 + 0.08 * breathe);

    // fisuras capilares saliendo del tronco
    float hairSeed = vnoise(vec2(p.y * 9.0 + uSeed * 3.1, uSeed));
    float hair = pow(hairSeed, 7.0)
      * smoothstep(0.4, 0.05, abs(p.x - cx)) * taper;
    col += uEdge * hair * 0.9;

    // RAYOS DE ENERGIA: 4 arcos quebrados que brotan del tronco y titilan
    // en loop (chispazos de electricidad escapando de la ruptura). Cada
    // uno nace en un punto distinto del tronco y crece/muere en su propia
    // ventana de tiempo -> nunca laten todos a la vez (continuo, sin
    // parpadeo global).
    float bolt = 0.0;
    for (int i = 0; i < 4; i += 1) {
      float fi = float(i);
      float cyc = fract(uTime * 0.35 + fi * 0.27 + uSeed * 0.11);
      // ventana de vida del rayo dentro de su ciclo (aparece, crece, muere)
      float life = smoothstep(0.0, 0.12, cyc) * smoothstep(0.62, 0.2, cyc);
      if (life < 0.01) {
        continue;
      }
      float originY = (hash(vec2(uSeed + fi * 3.1, 2.0)) - 0.5) * 0.68;
      float originX = cx + (vnoise(vec2(originY * 1.6 + uSeed, uSeed))
        - 0.5) * 0.5;
      float dirSign = hash(vec2(uSeed + fi * 5.7, 6.0)) > 0.5 ? 1.0 : -1.0;
      float ang = 0.35 + hash(vec2(uSeed + fi * 2.3, 8.0)) * 0.9;
      vec2 dir = vec2(dirSign * sin(ang), cos(ang) * 0.6 - 0.3);
      float len = (0.22 + hash(vec2(uSeed + fi, 4.0)) * 0.2) * life;
      float bd = boltDist(p, vec2(originX, originY), dir, max(len, 0.001),
        uTime + fi * 12.0);
      float core = smoothstep(0.028, 0.0, bd);
      float glow = smoothstep(0.09, 0.0, bd) * 0.5;
      bolt += (core + glow) * life;
    }
    col += mix(uEdge, vec3(1.0), 0.4) * bolt * 1.1;

    float alpha = max(inside * 0.96, eG);
    alpha = max(alpha, halo * 0.55);
    alpha = max(alpha, hair * 0.8);
    alpha = max(alpha, bolt * 0.9);
    if (alpha < 0.01) {
      discard;
    }
    gl_FragColor = vec4(col, alpha);
  }
`

// WORMHOLE (futuro/regreso): puente Einstein-Rosen — disco de streaks
// radiales difuminados que se tuercen y fluyen HACIA el centro (absorbe el
// espacio-tiempo), con LENTE GRAVITACIONAL explicita (el radio de muestreo
// se comprime cerca del horizonte, como si el propio espacio se doblara) +
// un anillo de fotones brillante justo en el horizonte (la imagen icónica
// de curvatura extrema), agujero central oscuro, borde emplumado que se
// difumina mas alla del disco. Paleta azul-blanco-gris (core = nucleo
// blanco, edge = azul del sentido). Movimiento continuo y fluido: cero
// glitch. El plane es CUADRADO (aspect 1). 1 draw call.
const WORMHOLE_FRAG = `
  uniform float uTime;
  uniform vec3 uCore;
  uniform vec3 uEdge;
  uniform float uSeed;
  uniform float uFringe;
  varying vec2 vUv;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453);
  }
  float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  void main() {
    vec2 p = (vUv - 0.5) * 2.0;
    float rRaw = length(p);
    float ang = atan(p.y, p.x);

    // borde del disco: ondulacion suave que gira lenta (fluida)
    float wob = vnoise(
      vec2(cos(ang), sin(ang)) * 1.6 + uSeed + uTime * 0.12
    );
    float R = 0.72 + (wob - 0.5) * 0.09;

    if (rRaw > R + 0.26) {
      discard;
    }

    // LENTE GRAVITACIONAL: el radio efectivo se comprime cerca del
    // horizonte (r/R se curva hacia adentro), como si la luz se doblara
    // al pasar cerca de la masa central. rRaw sigue guiando el
    // discard/feather (geometria real); r es el radio "curvado" que
    // alimenta el flujo y el color (la dilatacion visual). SIN clamp: si
    // se satura en un valor fijo para rRaw > R, todo el anillo exterior
    // (la pluma) queda con r CONSTANTE -> el ruido que depende de r se
    // congela ahi y se ve como una costura/linea recta cruzando el disco.
    float k = rRaw / R;
    float r = R * pow(k, 1.6);

    // remolino: torsion creciente hacia el centro + rotacion global
    float twist = ang + (1.0 - clamp(r / R, 0.0, 1.0)) * 2.6 + uTime * 0.3;

    // streaks radiales fluyendo HACIA el centro (absorcion), estirados por
    // la misma compresion de la lente -> se acumulan/aceleran al acercarse
    float s1 = vnoise(vec2(twist * 4.5, r * 2.2 + uTime * 1.5));
    float s2 = vnoise(vec2(twist * 10.0, r * 4.6 + uTime * 2.3));
    float flow = clamp(pow(s1 * 0.65 + s2 * 0.35, 1.5) * 1.25, 0.0, 1.0);

    // cuerpo: streaks brillantes sobre vacio; el centro es el agujero
    vec3 bright = mix(vec3(1.0), uCore, 0.35);
    vec3 col = mix(vec3(0.01, 0.012, 0.02), bright, flow);
    float hole = smoothstep(0.3, 0.05, r);
    col = mix(col, mix(vec3(0.0), uEdge, 0.15), hole);

    // anillo de acrecion sutil que late suave
    float accr = smoothstep(0.16, 0.0, abs(r - R * 0.62));
    col += uCore * accr * 0.35 * (0.7 + 0.3 * sin(uTime * 1.1 + uSeed));

    // ANILLO DE FOTONES: linea brillante y nitida justo en el horizonte de
    // eventos (rRaw, sin la compresion de la lente) — la firma visual de
    // un espacio-tiempo curvado al extremo.
    float photonRing = smoothstep(0.045, 0.0, abs(rRaw - R * 0.97));
    col += mix(vec3(1.0), uCore, 0.3) * photonRing
      * (0.8 + 0.2 * sin(uTime * 2.0 + uSeed));

    // pluma del borde: streaks difuminandose mas alla del disco (succion)
    float feather = smoothstep(R + 0.26, R - 0.04, rRaw)
      * smoothstep(R - 0.18, R, rRaw);
    col += mix(vec3(1.0), uEdge, 0.55) * feather * (0.4 + flow * 0.8);

    // fringe cromatico suave del borde (sobre el radio geometrico real)
    float ab = 0.02 * uFringe;
    col += uCore * smoothstep(0.05, 0.0, abs(rRaw - (R - ab))) * 0.35;
    col += uEdge * smoothstep(0.05, 0.0, abs(rRaw - (R + ab))) * 0.45;

    // alpha: disco opaco (radio geometrico real) + pluma que se desvanece
    float alpha = smoothstep(R + 0.02, R - 0.1, rRaw);
    alpha = max(alpha, feather * (0.35 + flow * 0.6));
    if (alpha < 0.01) {
      discard;
    }
    gl_FragColor = vec4(col, alpha);
  }
`

interface PortalRift {
  group: Group
  update(t: number): void
}

/**
 * FRACTURA DIMENSIONAL: el prop base de TODOS los portales del recorrido.
 * La forma la decide el estilo: 'crack' (grieta rota, CRACK_FRAG) o
 * 'wormhole' (disco absorbente, WORMHOLE_FRAG) — forma unica por uSeed —
 * + letrero y/o año opcionales. El grupo nace con origen en el PISO y la
 * fractura centrada en `cy`. 1-3 draw calls segun letreros (las esquirlas
 * poligonales se eliminaron 2026-07-10: leian como "triangulos random"
 * sueltos, sin lectura clara — decision del dueno).
 */
function dimensionalTear(opts: {
  kind: TearKind
  width: number
  height: number
  /** Centro vertical de la fractura (m sobre el piso). */
  cy: number
  seed: number
  sign?: string
  year?: string
}): PortalRift {
  const style = TEAR_STYLES[opts.kind]
  const crack = style.shape === 'crack'
  const material = new ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uCore: { value: new Color(style.core) },
      uEdge: { value: new Color(style.edge) },
      uSeed: { value: opts.seed },
      uAspect: { value: opts.width / opts.height },
      uFringe: { value: style.fringe },
    },
    vertexShader: TEAR_VERT,
    fragmentShader: crack ? CRACK_FRAG : WORMHOLE_FRAG,
    transparent: true,
    depthWrite: false,
  })
  const group = new Group()
  const tear = new Mesh(new PlaneGeometry(opts.width, opts.height), material)
  tear.position.set(0, opts.cy, 0.03)
  tear.userData.noOutline = true
  group.add(tear)
  if (opts.sign) {
    const tone = crack ? '#e8d8b0' : '#eafcff'
    const sign = label(opts.sign, { size: 0.16, color: tone })
    sign.position.set(0, opts.cy + opts.height * 0.44, 0.09)
    group.add(sign)
  }
  if (opts.year) {
    const year = label(opts.year, { size: 0.4, color: '#eafcff' })
    // el label hereda la rotacion del grupo: cuando el muro de salida lo
    // gira 180deg, la cara LEGIBLE queda mirando al jugador (no se espeja).
    year.position.set(0, opts.cy + 1.5, 0.06)
    year.userData.noOutline = true
    group.add(year)
  }
  return {
    group,
    update: (t) => {
      material.uniforms.uTime.value = t
      // la fractura respira apenas (continuo, sin saltos)
      const pulse = 1 + Math.sin(t * 1.7) * 0.012
      tear.scale.set(pulse, pulse, 1)
    },
  }
}

/**
 * PORTAL ENTRE SALAS (ida/regreso): WORMHOLE tipo puente Einstein-Rosen en
 * el muro sellado — disco de streaks difuminados absorbiendo el espacio,
 * lente gravitacional + anillo de fotones. `kind` fija la paleta (la
 * semantica del sentido): 'future' azul electrico/nucleo blanco, 'return'
 * azul-gris frio/nucleo blanco — paleta azul-blanco-gris (re-decidido por
 * el dueno 2026-07-10, 2da iteracion). Con `opts.year`, muestra el año de
 * la sala destino flotando arriba (decision que SE CONSERVA). 2 draw
 * calls (fractura + letrero del año).
 */
export function futurePortal(
  kind: 'future' | 'return',
  opts: { year?: string } = {},
): PortalRift {
  let seed = kind === 'future' ? 3.7 : 8.2
  for (const ch of opts.year ?? '') {
    seed += ch.charCodeAt(0) * 0.13
  }
  // plane CUADRADO: el disco del wormhole asume aspect 1
  return dimensionalTear({
    kind,
    width: 2.6,
    height: 2.6,
    cy: 1.4,
    seed,
    year: opts.year,
  })
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
  /** Año de la etapa (ya NO se muestra: el letrero solo dice ANTES). */
  year: string
  locale: Locale
  onEnter(roomIndex: number, spawn: { x: number; z: number }): void
}): PropHandle {
  // letrero solo "ANTES" (decision del usuario 2026-07-06): sin el año.
  const sign = opts.locale === 'es' ? 'ANTES' : 'BEFORE'
  // ponytail: opts.accent y opts.year ya no se usan (paleta por TEAR_STYLES,
  // letrero sin año); se conservan en la firma por los call sites de salas.
  const rift = dimensionalTear({
    kind: 'past',
    width: 2.2,
    height: 3.1,
    cy: 1.55,
    seed: 11.3 + opts.room.index * 2.7,
    sign,
  })
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
  const rift = dimensionalTear({
    kind: 'exit',
    width: 2.2,
    height: 3.1,
    cy: 1.55,
    seed: 5.1 + opts.roomIndex * 3.3,
    sign,
  })
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
  /** Oculta el pilar cilindrico procedural (la sala pone su propio GLB). */
  hidePillar?: boolean
  onOpen(title: string, paragraphs: readonly string[]): void
}): PropHandle {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  const trim = opts.theme.trim ?? opts.theme.accent
  const units = unitGeo()
  // pilar cilindrico (mismo lenguaje que el pedestal de contacto). El aula lo
  // oculta (hidePillar) y monta su pedestal.glb CC0 en su lugar; el cuaderno
  // flotante y el halo/luz siguen viniendo de aca.
  if (!opts.hidePillar) {
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
  }
  // cuaderno FLOTANDO separado del pilar: libro con VOLUMEN (portada/lomo
  // como caja delgada) + pagina con el texto al frente + halo del acento
  // detras (el pulso lo anima el update). La caja garantiza que desde
  // cualquier angulo se vea un objeto solido, nunca el reverso invisible
  // de un plane de una sola cara.
  const float = new Group()
  const cover = new Mesh(new BoxGeometry(0.66, 0.52, 0.06), toonMat(trim))
  cover.position.z = -0.03
  cover.castShadow = true
  const page = new Mesh(
    new PlaneGeometry(0.6, 0.48),
    new MeshBasicMaterial({ map: notebookTexture(opts.notebook) }),
  )
  page.position.z = 0.005
  page.userData.noOutline = true
  const haloMat = new MeshBasicMaterial({
    color: trim,
    transparent: true,
    opacity: 0.26,
  })
  const halo = new Mesh(new PlaneGeometry(0.76, 0.62), haloMat)
  halo.position.z = -0.08
  halo.userData.noOutline = true
  float.add(halo, cover, page)
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

/**
 * KIT INFORMATIVO ESTANDAR de la sala (decision del usuario 2026-07-04):
 * los 4 elementos que muestran el CV van en la MISMA posicion y tamaño en
 * TODAS las salas (el orden del aula, la primera sala, es el canon):
 *   - RETOS       -> muro -X (la DERECHA de quien avanza), a media sala.
 *   - APRENDIZAJES-> muro +X (su IZQUIERDA), a media sala (espejo).
 *   - grieta      -> muro +X al fondo (mano izquierda, junto a la salida).
 *   - cuaderno    -> centro geometrico de la sala (x=0, z=room.z),
 *     bloqueando el eje de transito, con el libro de frente a la entrada
 *     (plan journey-puerta-sillas-pilar: antes quedaba a un cuarto de la
 *     entrada, encimado con el spawn del jugador).
 * Las salas son uniformes (13.2 m), asi que las coordenadas resultantes
 * son identicas sala a sala — consistencia garantizada por construccion.
 */
export function infoKit(opts: {
  room: RoomLayout
  /** Año de la etapa (letrero ANTES · {año} de la grieta). */
  year: string
  theme: RoomTheme
  locale: Locale
  texts: RoomTexts
  /** Luz del cuaderno flotante (solo tier full). */
  withLight: boolean
  /** Sala sin pasado (ej. `futuro`): false omite la grieta. Default true. */
  withPortal?: boolean
  /** Estilo de las pizarras RETOS/APRENDIZAJES (default whiteboard oficina). */
  boardStyle?: BoardStyle
  /** Oculta el pilar procedural del cuaderno (la sala monta su GLB). */
  hidePillar?: boolean
  onFicha(roomIndex: number, kind: FichaKind): void
  onEnterPast(roomIndex: number, spawn: { x: number; z: number }): void
  onStory(title: string, paragraphs: readonly string[]): void
}): { props: PropHandle[]; colliders: Box2[] } {
  const { room, texts } = opts
  const half = room.width / 2
  const retos = fichaBoard({
    roomIndex: room.index,
    kind: 'retos',
    position: [-half + 0.35, 0, room.z - 0.6],
    rotationY: Math.PI / 2,
    theme: opts.theme,
    locale: opts.locale,
    preview: texts.retos,
    boardStyle: opts.boardStyle,
    onOpen: opts.onFicha,
  })
  const aprendizajes = fichaBoard({
    roomIndex: room.index,
    kind: 'aprendizajes',
    position: [half - 0.35, 0, room.z - 0.6],
    rotationY: -Math.PI / 2,
    theme: opts.theme,
    locale: opts.locale,
    preview: texts.aprendizajes,
    boardStyle: opts.boardStyle,
    onOpen: opts.onFicha,
  })
  const portal =
    opts.withPortal === false
      ? null
      : pastPortal({
          room,
          position: [half - 0.1, 0, room.z + 5.2],
          rotationY: -Math.PI / 2,
          accent: opts.theme.accent,
          year: opts.year,
          locale: opts.locale,
          onEnter: opts.onEnterPast,
        })
  // Centro geometrico de la sala (x=0, z=room.z), en el eje de transito:
  // el jugador lo encuentra de frente al entrar y debe rodearlo (plan
  // journey-puerta-sillas-pilar; ya no se superpone con el spawn). El giro
  // de 180 grados deja la cara frontal del libro mirando a la entrada.
  const nota = lecternNotebook({
    roomIndex: room.index,
    position: [0, 0, room.z],
    rotationY: Math.PI,
    theme: opts.theme,
    notebook: { title: texts.title, lines: texts.notebook },
    story: { title: texts.title, paragraphs: texts.resena },
    withLight: opts.withLight,
    hidePillar: opts.hidePillar,
    onOpen: opts.onStory,
  })
  return {
    props: portal
      ? [retos, aprendizajes, portal, nota]
      : [retos, aprendizajes, nota],
    colliders: [footprint(0, room.z, 1, 1)],
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

// ---------------------------------------------------------------------------
// CANON DE SALA (plan journey-salas-estandar): officeLayout, npcCoworkers,
// wallArt y softwareShowcase — los 4 helpers que replican todas las salas.
// Ver docs/specs/journey-salas-estandar/02-el-canon-de-sala.md.
// ---------------------------------------------------------------------------

export interface OfficeLayout {
  group: Group
  colliders: Box2[]
  /** ScreenSwap de las laptops togglables (puestos SIN NPC), para E. */
  toggles: { spot: number; screen: ScreenSwap }[]
  /** Interactables de "sentarse" para los puestos SIN NPC (silla vacia). */
  seats: Interactable[]
  /** Libera TODAS las variantes de pantalla (disposeDeep solo ve la activa). */
  dispose(): void
}

const SIT_LABEL = { es: 'Sentarse', en: 'Sit down' } as const
const STAND_LABEL = { es: 'Levantarse', en: 'Stand up' } as const

/**
 * Interactable de silla vacia sentable: toggle Sentarse/Levantarse que
 * muta state.playerSeat directo, leyendo el estado REAL (si el jugador se
 * sento en OTRA silla primero, el label no queda desincronizado). Lo usan
 * officeLayout (puestos sin NPC) y el aula (layout a mano).
 */
export function seatInteractable(
  id: string,
  x: number,
  z: number,
  state: EngineState,
  opts?: {
    /** Orientacion del jugador sentado (default 0 = mira +Z). */
    rotationY?: number
    /** Pose sentada: 'typing' si la silla esta frente a una PC. */
    pose?: 'sit' | 'typing'
    /** Se dispara al sentarse (true) / levantarse (false) en esta silla:
     *  la sala lo usa para encender/apagar la PC del puesto. */
    onSeatChange?: (seated: boolean) => void
  },
): Interactable {
  const item: Interactable = {
    id,
    x,
    z,
    radius: 1.4,
    label: { ...SIT_LABEL },
    onActivate: () => {
      const sameSeat = state.playerSeat?.x === x && state.playerSeat?.z === z
      state.playerSeat = sameSeat
        ? null
        : { x, z, rotationY: opts?.rotationY ?? 0, pose: opts?.pose }
      item.label = sameSeat ? { ...SIT_LABEL } : { ...STAND_LABEL }
      opts?.onSeatChange?.(!sameSeat)
    },
  }
  return item
}

/**
 * Filas de oficina fusionadas: escritorios + sillas en 1 lote outlined
 * (2 draw calls) + una laptop por puesto. Las laptops de los puestos con
 * NPC (poweredSpots) arrancan ENCENDIDAS; las libres quedan en `toggles`
 * para que la sala las haga encendibles con E (patron del aula).
 */
export function officeLayout(opts: {
  /** Centros [x,z] de cada puesto; la silla queda en z-0.55 mirando +Z. */
  spots: readonly (readonly [number, number])[]
  /** Color del mobiliario (tono del rubro). */
  color: string
  /** Puestos (indice en spots) con laptop ENCENDIDA (NPC sentado). */
  poweredSpots?: ReadonlySet<number>
  /** Tema para las pantallas de las laptops encendidas. */
  screenTheme: Pick<RoomTheme, 'screenBg' | 'screenFg' | 'ink'>
  /** Contenido de pantalla por puesto (loop de codigo del rubro). */
  screenFor?: (index: number) => { title: string; lines: readonly string[] }
  /** Estilo de pantalla por puesto: 'linux' (terminal) o 'ide' (editor de
   *  código). Default: alterna linux/ide por puesto para dar variedad
   *  (pedido del dueño: monitores de dev Linux + algún IDE). */
  screenKindFor?: (index: number) => 'linux' | 'ide'
  /** Identificador de la sala, para ids unicos del interactable de silla. */
  roomIndex: number
  /** Estado del motor: el toggle de sentarse muta state.playerSeat directo. */
  state: EngineState
  /** Opt-in T4: escritorios/sillas GLB CC0 en vez de las cajas fusionadas
   *  (solo lo pasan las salas migradas; el resto conserva el merge).
   *  `deskWidth`/`chairWidth` afinan la auto-escala por pack (el sci-fi de
   *  futuro es mas grande que el Kenney plano). */
  furniture?: {
    deskUrl: string
    chairUrl: string
    deskWidth?: number
    chairWidth?: number
  }
}): OfficeLayout {
  const powered = opts.poweredSpots ?? new Set<number>()
  const group = new Group()
  const colliders: Box2[] = []
  const toggles: { spot: number; screen: ScreenSwap }[] = []
  const seats: Interactable[] = []
  const screens: ScreenSwap[] = []
  // silla de un puesto mirando al frente (+Z): asiento + respaldo + patas
  const chairParts = (x: number, cz: number) => [
    { w: 0.42, h: 0.05, d: 0.42, x, y: 0.44, z: cz },
    { w: 0.42, h: 0.5, d: 0.05, x, y: 0.72, z: cz - 0.2 },
    { w: 0.05, h: 0.44, d: 0.05, x: x - 0.17, y: 0.22, z: cz - 0.1 },
    { w: 0.05, h: 0.44, d: 0.05, x: x + 0.17, y: 0.22, z: cz - 0.1 },
  ]
  if (opts.furniture) {
    // T4: escritorio + silla GLB CC0 en cada puesto (mismas posiciones)
    const deskWidth = opts.furniture.deskWidth ?? 1.15
    const chairWidth = opts.furniture.chairWidth ?? 0.52
    for (const [x, z] of opts.spots) {
      group.add(
        placeFurniture({
          url: opts.furniture.deskUrl,
          x,
          z,
          targetWidth: deskWidth,
        }),
      )
      group.add(
        placeFurniture({
          url: opts.furniture.chairUrl,
          x,
          z: z - 0.55,
          targetWidth: chairWidth,
        }),
      )
    }
  } else {
    group.add(
      outlinedMergedBoxes(
        opts.spots.flatMap(([x, z]) => [
          { w: 1.1, h: 0.05, d: 0.6, x, y: 0.72, z },
          { w: 0.06, h: 0.72, d: 0.55, x: x - 0.5, y: 0.36, z },
          { w: 0.06, h: 0.72, d: 0.55, x: x + 0.5, y: 0.36, z },
          ...chairParts(x, z - 0.55),
        ]),
        toonMat(opts.color),
        { inflate: 0.035, castShadow: true },
      ),
    )
  }
  const offVariant = {
    lines: [],
    theme: {
      screenBg: '#08080c',
      screenFg: '#22301c',
      ink: opts.screenTheme.ink,
    },
    dot: '#b23a3a',
  }
  opts.spots.forEach(([x, z], index) => {
    colliders.push(footprint(x, z, 1.3, 0.8), footprint(x, z - 0.55, 0.5, 0.5))
    const code = opts.screenFor?.(index) ?? { title: '', lines: [] }
    // linux (terminal) por defecto; alterna a ide (editor) en puestos impares
    // para variar (pedido del dueño). La sala puede forzar con screenKindFor.
    const screenKind =
      opts.screenKindFor?.(index) ?? (index % 2 === 1 ? 'ide' : 'linux')
    const { group: monitorGroup, screen } = switchableMonitor({
      position: [x, 0.72, z + 0.05],
      rotationY: Math.PI,
      width: 0.46,
      variants: {
        off: offVariant,
        on: {
          title: code.title,
          lines: code.lines,
          theme: opts.screenTheme,
          dot: '#3f9d63',
          kind: screenKind,
        },
      },
      initial: powered.has(index) ? 'on' : 'off',
    })
    group.add(monitorGroup)
    screens.push(screen)
    if (!powered.has(index)) {
      toggles.push({ spot: index, screen })
      seats.push(
        seatInteractable(
          `silla-${opts.roomIndex}-${index}`,
          x,
          z - 0.55,
          opts.state,
        ),
      )
    }
  })
  return {
    group,
    colliders,
    toggles,
    seats,
    dispose: () => {
      for (const screen of screens) {
        screen.dispose()
      }
    },
  }
}

/** Enfoque narrativo del NPC (estandar de 2 enfoques, decision 3). */
export type CoworkerRole = 'coworker' | 'staff' | 'boss'

export interface CoworkerDef {
  key: string
  /** Enfoque: compañero de desarrollo / personal del sitio / jefe. */
  role: CoworkerRole
  spec: CharacterSpec
  position: readonly [number, number, number]
  rotationY?: number
  /** Poses sentadas admitidas para un coworker (typing = tecleando). */
  pose?: 'sit' | 'kneel' | 'typing' | 'sitTalk'
  /** Si esta sentado, al conversar se levanta y gesticula de pie (opt-in). */
  standToTalk?: boolean
  path?: readonly (readonly [number, number])[]
  speed?: number
  dialog: NpcDialog
}

/**
 * NPCs conversables de la sala con los 2 enfoques del estandar:
 * encapsula el patron makeNpc + npcTalk. En DEV valida el mix
 * (>=2 'coworker' + >=2 'staff' — AC-5) salvo `validateMix: false`
 * (el aula esta exenta del mix).
 */
export function npcCoworkers(opts: {
  roomIndex: number
  npcs: readonly CoworkerDef[]
  openDialog: OpenDialog
  /** Valida el mix del estandar en DEV (default true). */
  validateMix?: boolean
}): { npcs: NpcHandle[]; talks: NpcTalk[] } {
  if (import.meta.env.DEV && opts.validateMix !== false) {
    const count = (role: CoworkerRole): number =>
      opts.npcs.filter((npc) => npc.role === role).length
    if (count('coworker') < 2 || count('staff') < 2) {
      console.error(
        `[journey] npcCoworkers sala ${opts.roomIndex}: el estandar pide ` +
          ">=2 'coworker' + >=2 'staff' (AC-5)",
      )
    }
  }
  const npcs: NpcHandle[] = []
  const talks: NpcTalk[] = []
  for (const def of opts.npcs) {
    const npc = makeNpc({
      ...def.spec,
      position: def.position,
      rotationY: def.rotationY,
      pose: def.pose,
      standToTalk: def.standToTalk,
      path: def.path,
      speed: def.speed,
    })
    npcs.push(npc)
    talks.push(
      npcTalk({
        id: `talk-${opts.roomIndex}-${def.key}`,
        npc,
        dialog: def.dialog,
        openDialog: opts.openDialog,
      }),
    )
  }
  return { npcs, talks }
}

export interface WallFrame {
  key: string
  position: readonly [number, number, number]
  rotationY?: number
  /** Ancho x alto de la lamina (default 1.1 x 0.8). */
  size?: readonly [number, number]
  /** Lamina Canvas del rubro (tinta plana, estilo manga). */
  draw: DrawFn
  /** Si es inspeccionable: E abre esta ficha en el panel DOM. */
  ficha?: {
    title: Record<Locale, string>
    paragraphs: Record<Locale, readonly string[]>
  }
}

const FRAME_LABEL = {
  es: 'Mirar el cuadro',
  en: 'Look at the picture',
} as const

/**
 * Cuadros de rubro en la pared: laminas Canvas con marco (trim del theme).
 * Los marcos de TODOS los cuadros se fusionan en 1 mesh; cada lamina es 1
 * plane con su textura. 1-2 por sala llevan `ficha` (E abre panel — AC-7).
 */
export function wallArt(opts: {
  roomIndex: number
  theme: Pick<RoomTheme, 'trim' | 'ink' | 'accent'>
  locale: Locale
  frames: readonly WallFrame[]
  onFicha(title: string, paragraphs: readonly string[]): void
  /** Color del marco (default `trim` del theme; ej. madera para pizarras). */
  frameColor?: string
}): { props: PropHandle[]; colliders: Box2[] } {
  const trim = opts.frameColor ?? opts.theme.trim ?? opts.theme.accent
  const marcoGroup = new Group()
  // outlinedMergedBoxes (no mergedBoxes + outline generico): el contorno
  // de un merge con posiciones horneadas se desplaza del marco al escalar
  // alrededor del origen local — el mismo bug que documenta toon.ts.
  marcoGroup.add(
    outlinedMergedBoxes(
      opts.frames.map((frame) => {
        const [w, h] = frame.size ?? [1.1, 0.8]
        const rotY = frame.rotationY ?? 0
        return {
          w: w + 0.1,
          h: h + 0.1,
          d: 0.05,
          x: frame.position[0] - Math.sin(rotY) * 0.035,
          y: frame.position[1],
          z: frame.position[2] - Math.cos(rotY) * 0.035,
          rotY,
        }
      }),
      toonMat(trim),
    ),
  )
  const props: PropHandle[] = [{ group: marcoGroup }]
  for (const frame of opts.frames) {
    const [w, h] = frame.size ?? [1.1, 0.8]
    const art = new Mesh(
      new PlaneGeometry(w, h),
      new MeshBasicMaterial({ map: makeCanvasTexture(256, frame.draw) }),
    )
    art.position.set(frame.position[0], frame.position[1], frame.position[2])
    art.rotation.y = frame.rotationY ?? 0
    art.userData.noOutline = true
    const group = new Group()
    group.add(art)
    const handle: PropHandle = { group }
    const ficha = frame.ficha
    if (ficha) {
      handle.interactable = {
        id: `cuadro-${opts.roomIndex}-${frame.key}`,
        x: frame.position[0],
        z: frame.position[2],
        radius: 2,
        label: FRAME_LABEL,
        onActivate: () =>
          opts.onFicha(ficha.title[opts.locale], ficha.paragraphs[opts.locale]),
      }
    }
    props.push(handle)
  }
  return { props, colliders: [] }
}

export interface ShowcaseDemo {
  key: string
  /** Titulo mostrado en el monitor y en el panel. */
  title: Record<Locale, string>
  /** Loop Canvas ambiente del monitor (t en segundos, ~7 fps). */
  draw(ctx: CanvasRenderingContext2D, size: number, t: number): void
  /** Panel HTML operable (se abre al pulsar E cerca). */
  panel: {
    /** Color de branding del sistema real. */
    brand: string
    /** Markup del mockup (buscador, tabla, cards...), por locale. */
    html: Record<Locale, string>
  }
}

const SHOWCASE_LABEL = {
  es: 'Ver la demo del sistema',
  en: 'View the system demo',
} as const

/**
 * Showcase de software junto a la puerta (AC-6): totem con monitor Canvas
 * en loop (demo activa, ~7 fps) + panel HTML operable via `openShowcase`.
 * E (o el boton del panel) cicla a la siguiente demo — el monitor 3D y el
 * panel se actualizan juntos. Todas las salas presentes menos el aula.
 */
export function softwareShowcase(opts: {
  roomIndex: number
  /** Distingue multiples showcases en una sala (ej. las 2 areas). */
  key?: string
  position: readonly [number, number, number]
  rotationY?: number
  theme: Pick<RoomTheme, 'screenBg' | 'screenFg' | 'ink' | 'accent' | 'trim'>
  locale: Locale
  /** Demos del sistema real; E cicla a la siguiente. */
  demos: readonly ShowcaseDemo[]
  /** Abre el panel HTML del HUD (UI action `openShowcase`). */
  openShowcase(ref: ShowcaseRef): void
}): PropHandle {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // totem: base + mastil + marco de la pantalla grande
  const stand = mergedBoxes(
    [
      { w: 0.7, h: 0.1, d: 0.5, x: 0, y: 0.05, z: 0 },
      { w: 0.12, h: 1, d: 0.12, x: 0, y: 0.55, z: 0 },
      { w: 1.34, h: 0.88, d: 0.07, x: 0, y: 1.5, z: -0.02 },
    ],
    toonMat('#15151a'),
  )
  stand.castShadow = true
  // pantalla canvas animada: la demo activa redibuja ~7 fps
  const size = 256
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const maybeCtx = canvas.getContext('2d')
  if (!maybeCtx) {
    throw new Error('softwareShowcase: canvas 2d no disponible')
  }
  const context2d = maybeCtx
  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  const screen = new Mesh(
    new PlaneGeometry(1.24, 0.78),
    new MeshBasicMaterial({ map: texture }),
  )
  screen.position.set(0, 1.5, 0.02)
  screen.userData.noOutline = true
  group.add(stand, screen)

  let active = 0
  let needsDraw = true
  let last = -1

  function demoAt(index: number): ShowcaseDemo {
    const demo = opts.demos[index]
    if (!demo) {
      throw new Error(`softwareShowcase: demo ${index} fuera de rango`)
    }
    return demo
  }

  function drawScreen(t: number): void {
    const demo = demoAt(active)
    demo.draw(context2d, size, t)
    // barra inferior: titulo + posicion en el ciclo + hint [E]
    context2d.fillStyle = 'rgba(10,10,14,0.85)'
    context2d.fillRect(0, size - 34, size, 34)
    context2d.textBaseline = 'alphabetic'
    context2d.textAlign = 'left'
    context2d.fillStyle = opts.theme.screenFg
    context2d.font = `bold 17px ${MANGA_FONT}`
    context2d.fillText(demo.title[opts.locale].slice(0, 22), 10, size - 12)
    context2d.textAlign = 'right'
    context2d.fillText(
      `${active + 1}/${opts.demos.length} · [E]`,
      size - 10,
      size - 12,
    )
    context2d.textAlign = 'left'
    texture.needsUpdate = true
  }

  function view(): ShowcaseView {
    const demo = demoAt(active)
    return {
      title: demo.title[opts.locale],
      brand: demo.panel.brand,
      html: demo.panel.html[opts.locale],
      position: `${active + 1}/${opts.demos.length}`,
    }
  }

  const ref: ShowcaseRef = {
    view,
    next: () => {
      active = (active + 1) % opts.demos.length
      needsDraw = true
      return view()
    },
  }

  return {
    group,
    interactable: {
      id: `showcase-${opts.roomIndex}-${opts.key ?? 'main'}`,
      x: opts.position[0],
      z: opts.position[2],
      radius: 2.2,
      label: SHOWCASE_LABEL,
      onActivate: () => opts.openShowcase(ref),
    },
    update: (t) => {
      if (needsDraw || t - last > 0.14) {
        needsDraw = false
        last = t
        drawScreen(t)
      }
    },
  }
}
