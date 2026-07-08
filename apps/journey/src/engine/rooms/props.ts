/**
 * @module rooms/props (engine)
 * @description Props procedurales compartidos entre salas manga-ink:
 *   escritorio, monitor (estatico e intercambiable), pizarra de ficha con
 *   titulo + tiza, GRIETA TEMPORAL al pasado (rasgadura con vortice-reloj),
 *   pedestal con el cuaderno-reseña FLOTANTE de la etapa, pila de papeles
 *   y los 4 helpers del CANON de sala (plan journey-salas-estandar):
 *   officeLayout, npcCoworkers, wallArt y softwareShowcase. Todo
 *   primitivas del pool toon — cero .glb, cero red.
 */
import {
  BoxGeometry,
  CanvasTexture,
  CircleGeometry,
  Color,
  Group,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
  PointLight,
  RingGeometry,
  ShaderMaterial,
  SRGBColorSpace,
  type Texture,
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

const PORTAL_LABEL = {
  es: 'Cruzar al pasado',
  en: 'Step into the past',
} as const

const EXIT_LABEL = {
  es: 'Volver al presente',
  en: 'Return to the present',
} as const

/** Color unico de TODAS las grietas al pasado: marron/sepia (el "antes"). */
const RIFT_SEPIA = '#c8a878'

/**
 * Esfera de reloj SEPIA vista de frente, para apoyar PLANA en el piso bajo
 * la grieta (el reloj ya no vive dentro de la grieta: decision del usuario
 * 2026-07-06). Marcas horarias + agujas 10:10 horneadas — 1 draw call.
 */
function floorClockTexture(): CanvasTexture {
  return makeCanvasTexture(256, (ctx, size) => {
    const c = size / 2
    ctx.clearRect(0, 0, size, size)
    // esfera crema con aro sepia
    ctx.fillStyle = '#e8d8b0'
    ctx.beginPath()
    ctx.arc(c, c, c - 6, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#6b4a2a'
    ctx.lineWidth = 9
    ctx.stroke()
    // marcas horarias
    for (let i = 0; i < 12; i += 1) {
      const angle = (i / 12) * Math.PI * 2
      const r0 = c - 16
      const r1 = i % 3 === 0 ? c - 38 : c - 26
      ctx.lineWidth = i % 3 === 0 ? 7 : 3
      ctx.beginPath()
      ctx.moveTo(c + Math.cos(angle) * r0, c + Math.sin(angle) * r0)
      ctx.lineTo(c + Math.cos(angle) * r1, c + Math.sin(angle) * r1)
      ctx.stroke()
    }
    // agujas 10:10 (clasico) horneadas
    ctx.strokeStyle = '#3a2416'
    ctx.lineCap = 'round'
    const hand = (angle: number, len: number, w: number) => {
      ctx.lineWidth = w
      ctx.beginPath()
      ctx.moveTo(c, c)
      ctx.lineTo(c + Math.cos(angle) * len, c + Math.sin(angle) * len)
      ctx.stroke()
    }
    hand(-Math.PI / 2 - Math.PI / 6, c * 0.48, 10)
    hand(-Math.PI / 2 + Math.PI / 6, c * 0.68, 7)
    ctx.fillStyle = '#3a2416'
    ctx.beginPath()
    ctx.arc(c, c, 9, 0, Math.PI * 2)
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
  /** Alimenta la ventana del portal con el snapshot de la sala destino
   *  (render-to-texture). El `futurePortal` lo implementa; `timeRift` no. */
  setPreview?(tex: Texture): void
}

/**
 * GRIETA TEMPORAL al pasado (rediseño 2026-07-06, decision del usuario):
 * rasgadura SEPIA irregular pegada plana al muro — SIN marco ni arco — SOLO
 * la grieta (el vortice-reloj y las motas se quitaron). El reloj ahora vive
 * de PIE en el piso, bajo la grieta. Todas las grietas son marron/sepia (el
 * "antes"). Letrero arriba + marca oscura + reloj en el piso. ~2.9 m de alto.
 * Es el portal al PASADO; la ida/regreso entre salas usa `futurePortal`.
 */
function timeRift(signText: string): PortalRift {
  const group = new Group()
  const rift = new Mesh(
    new PlaneGeometry(2.7, 3),
    new MeshBasicMaterial({ map: riftTexture(RIFT_SEPIA), transparent: true }),
  )
  rift.position.set(0, 1.5, 0.04)
  rift.userData.noOutline = true
  const sign = label(signText, { size: 0.16, color: '#e8d8b0' })
  sign.position.set(0, 2.88, 0.09)
  const scorch = new Mesh(unitGeo().plane, toonMat('#15101c'))
  scorch.rotation.x = -Math.PI / 2
  scorch.scale.set(2.1, 1.3, 1)
  scorch.position.set(0, 0.014, 0.5)
  scorch.userData.noOutline = true
  // reloj SEPIA de piso bajo la grieta (el reloj ya no vive adentro)
  const clock = new Mesh(
    new CircleGeometry(0.42, 40),
    new MeshBasicMaterial({ map: floorClockTexture() }),
  )
  clock.rotation.x = -Math.PI / 2
  clock.position.set(0, 0.02, 0.55)
  clock.userData.noOutline = true
  group.add(rift, sign, scorch, clock)
  return {
    group,
    update: (t) => {
      // la grieta respira apenas (el reloj de piso es estatico)
      const pulse = 1 + Math.sin(t * 2.1) * 0.015
      rift.scale.set(pulse, pulse, 1)
    },
  }
}

const PORTAL_VERT = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

// Superficie de energia del portal: vortice espiral + rayos/electricidad
// procedurales animados por uTime + ventana translucida con el snapshot de la
// sala destino (uPreview). Todo en 1 fragment shader -> 1 draw call.
const PORTAL_FRAG = `
  uniform float uTime;
  uniform vec3 uAccent;
  uniform sampler2D uPreview;
  uniform float uHasPreview;
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
    vec2 p = vUv - 0.5;
    float r = length(p) * 2.0;
    if (r > 1.0) discard;
    float ang = atan(p.y, p.x);

    // gradiente radial: nucleo brillante -> acento -> borde oscuro
    vec3 core = vec3(0.95, 0.98, 1.0);
    vec3 col = mix(core, uAccent, smoothstep(0.0, 0.35, r));
    col = mix(col, vec3(0.02, 0.03, 0.07), smoothstep(0.5, 1.0, r));

    // vortice espiral (3 brazos) girando -> "otra dimension"
    float spiral = 0.5 + 0.5 * sin((ang - r * 7.0 + uTime * 0.6) * 3.0);
    col += uAccent * spiral * (0.4 * (1.0 - r));

    // anillos de energia expandiendose
    float rings = 0.5 + 0.5 * sin(r * 26.0 - uTime * 3.0);
    col += uAccent * pow(rings, 3.0) * 0.16;

    // rayos / electricidad: filamentos radiales titilando hacia el borde
    float jitter = vnoise(vec2(ang * 3.0, uTime * 2.0));
    float fil = abs(sin(ang * 20.0 + jitter * 6.2831 + uTime * 1.4));
    float bolt = pow(1.0 - fil, 26.0) * smoothstep(0.15, 1.0, r);
    bolt *= step(0.55, hash(vec2(floor(ang * 5.0), floor(uTime * 8.0))));
    col += vec3(0.75, 0.88, 1.0) * bolt * 1.5;

    // ventana translucida: guiño de la sala destino en el centro
    vec3 preview = mix(uAccent * 0.45, texture2D(uPreview, vUv).rgb, uHasPreview);
    float win = smoothstep(0.72, 0.12, r);
    col = mix(col, preview, win * 0.5);

    // brillo glassy sutil hacia el centro
    col += vec3(0.06) * smoothstep(0.6, 0.0, r);

    float alpha = 0.96 * smoothstep(1.0, 0.86, r);
    gl_FragColor = vec4(col, alpha);
  }
`

/** Textura fallback 2x2 (tinte del acento) para el sampler uPreview mientras
 *  no haya snapshot de la sala destino. */
function portalFallbackTex(accent: string): CanvasTexture {
  return makeCanvasTexture(2, (ctx, size) => {
    ctx.fillStyle = accent
    ctx.fillRect(0, 0, size, size)
  })
}

function portalEnergyMaterial(accent: string): ShaderMaterial {
  return new ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uAccent: { value: new Color(accent) },
      uPreview: { value: portalFallbackTex(accent) },
      uHasPreview: { value: 0 },
    },
    vertexShader: PORTAL_VERT,
    fragmentShader: PORTAL_FRAG,
    transparent: true,
    depthWrite: false,
  })
}

/**
 * PORTAL AL FUTURO / DE REGRESO: reemplaza a la puerta entre salas. Oval con
 * superficie de energia SHADER (vortice + rayos/electricidad procedurales que
 * giran por uTime) y una VENTANA translucida que insinua la sala destino via
 * `setPreview` (render-to-texture; cae a un tinte del acento mientras no haya
 * snapshot). Color FIJO segun el sentido (decision del usuario 2026-07-06):
 * azul fosforecente al FUTURO, azul celeste (mas claro) al REGRESO — NO el
 * acento del rubro. Con `opts.year`, muestra el año de la sala destino
 * flotando arriba. Va pegado al muro sellado — la ventana es una ilusion
 * del shader, NO un vano real. 2-3 draw calls (energia + marco + año).
 */
export function futurePortal(
  accent: string,
  opts: { year?: string } = {},
): PortalRift {
  const group = new Group()
  const cy = 1.4
  const material = portalEnergyMaterial(accent)
  const energy = new Mesh(new CircleGeometry(1, 48), material)
  energy.scale.set(0.8, 1.12, 1)
  energy.position.set(0, cy, 0.02)
  energy.userData.noOutline = true
  const frame = new Mesh(
    new RingGeometry(1, 1.14, 48),
    new MeshBasicMaterial({ color: accent }),
  )
  frame.scale.set(0.8, 1.12, 1)
  frame.position.set(0, cy, 0.03)
  frame.userData.noOutline = true
  group.add(energy, frame)
  // año de la sala destino, flotando ARRIBA del portal
  if (opts.year) {
    const yearTag = label(opts.year, { size: 0.4, color: '#eaf6ff' })
    yearTag.position.set(0, cy + 1.5, 0.06)
    // el label hereda la rotacion del grupo: cuando el muro de salida lo
    // gira 180deg, la cara LEGIBLE queda mirando al jugador (no se espeja).
    yearTag.userData.noOutline = true
    group.add(yearTag)
  }
  return {
    group,
    update: (t) => {
      material.uniforms.uTime.value = t
      const pulse = 1 + Math.sin(t * 2.4) * 0.02
      frame.scale.set(0.8 * pulse, 1.12 * pulse, 1)
    },
    setPreview: (tex) => {
      material.uniforms.uPreview.value = tex
      material.uniforms.uHasPreview.value = 1
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
  /** Año de la etapa (ya NO se muestra: el letrero solo dice ANTES). */
  year: string
  locale: Locale
  onEnter(roomIndex: number, spawn: { x: number; z: number }): void
}): PropHandle {
  // letrero solo "ANTES" (decision del usuario 2026-07-06): sin el año.
  const sign = opts.locale === 'es' ? 'ANTES' : 'BEFORE'
  // ponytail: opts.accent y opts.year ya no se usan (grietas siempre sepia,
  // letrero sin año); se conservan en la firma por los call sites de salas.
  const rift = timeRift(sign)
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
  const rift = timeRift(sign)
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
): Interactable {
  const item: Interactable = {
    id,
    x,
    z,
    radius: 1.4,
    label: { ...SIT_LABEL },
    onActivate: () => {
      const sameSeat = state.playerSeat?.x === x && state.playerSeat?.z === z
      state.playerSeat = sameSeat ? null : { x, z, rotationY: 0 }
      item.label = sameSeat ? { ...SIT_LABEL } : { ...STAND_LABEL }
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
  pose?: 'sit' | 'kneel'
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
