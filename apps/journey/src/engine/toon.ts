/**
 * @module toon (engine)
 * @description Base visual toon del motor vanilla: pool GLOBAL de
 *   MeshToonMaterial (compartir material = menos state changes y shaders
 *   compilados 1 sola vez), gradientes de 3 escalones duros, texturas canvas
 *   de tinta deterministas (LCG), labels con lettering manga (reemplazan al
 *   Text SDF anterior) y disposeDeep con guard `userData.shared` para nunca
 *   liberar el pool. Los contornos inverted-hull se eliminaron (2026-07-07):
 *   `outlineGroup`/`outlinedMergedBoxes` quedan sin borde.
 *
 *   Nota DS: los hex son colores de MATERIAL WebGL/canvas, no CSS del UI.
 */
import {
  BoxGeometry,
  CanvasTexture,
  CapsuleGeometry,
  Color,
  type ColorRepresentation,
  CylinderGeometry,
  Group,
  type Material,
  Mesh,
  MeshBasicMaterial,
  MeshToonMaterial,
  NearestFilter,
  type Object3D,
  PlaneGeometry,
  RepeatWrapping,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
} from 'three'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import type { RoomTheme } from './themes'

/** Tinta universal de contornos y trazos (negro-azulado manga). */
export const INK = '#0b0b10'

export const MANGA_FONT = '"Space Grotesk", system-ui, sans-serif'
export const MONO_FONT = '"Space Mono", ui-monospace, monospace'

// La anisotropia por tier la fija app.ts ANTES de construir el mundo
// (full: 4, reduced: 2 — presupuesto del plan).
let anisotropy = 4

export function configureToon(opts: { anisotropy?: number }): void {
  if (opts.anisotropy !== undefined) {
    anisotropy = opts.anisotropy
  }
}

/** LCG determinista (mulberry32) — cada carga pinta identico. */
export function makeRng(seed: number): () => number {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let t = state
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** FNV-1a: semilla estable desde una key de texto (temas, labels). */
function hashSeed(text: string): number {
  let hash = 2166136261
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

export type DrawFn = (ctx: CanvasRenderingContext2D, size: number) => void

export function makeCanvasTexture(size: number, draw: DrawFn): CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('toon: canvas 2d context no disponible')
  }
  draw(ctx, size)
  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  texture.wrapS = RepeatWrapping
  texture.wrapT = RepeatWrapping
  texture.anisotropy = anisotropy
  return texture
}

// ---------------------------------------------------------------------------
// Gradientes toon (escalones duros)
// ---------------------------------------------------------------------------

const gradientCache = new Map<string, CanvasTexture>()

/** Escalones neutros por defecto (sombra dura tipo tinta). */
export const DEFAULT_GRADIENT: readonly [string, string, string] = [
  '#3a3a46',
  '#9a97a8',
  '#ffffff',
]

/**
 * Gradiente cel-shading "Arcane" para personajes con textura de cara: 3 bandas
 * con SALTO DURO y una sombra mas marcada (pero que no aplasta la piel), para
 * un corte cartoon/ilustracion mas pronunciado sobre la textura real. Pedido
 * del dueno 2026-07-08 (subir el cel-shading vs la version -lite anterior). Se
 * usa con `color: white` + `map` en toonMat: el gradientMap modula la luz en
 * bandas sin teñir la textura. El zocalo oscuro (#5a5560) da la sombra de
 * ilustracion; el salto directo a #e8e6ee marca el corte.
 */
export const CHARACTER_GRADIENT: readonly [string, string, string] = [
  '#5a5560',
  '#e8e6ee',
  '#ffffff',
]

/**
 * @function makeToonGradient
 * @description Canvas Nx1 con NearestFilter: los "saltos" de luz duros del
 *   cel shading. Cacheado y compartido (disposeDeep nunca lo libera).
 */
export function makeToonGradient(stops: readonly string[]): CanvasTexture {
  const key = stops.join('|')
  const cached = gradientCache.get(key)
  if (cached) {
    return cached
  }
  const canvas = document.createElement('canvas')
  canvas.width = stops.length
  canvas.height = 1
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('toon: canvas 2d context no disponible')
  }
  stops.forEach((stop, i) => {
    ctx.fillStyle = stop
    ctx.fillRect(i, 0, 1, 1)
  })
  const texture = new CanvasTexture(canvas)
  texture.minFilter = NearestFilter
  texture.magFilter = NearestFilter
  texture.userData.shared = true
  gradientCache.set(key, texture)
  return texture
}

// ---------------------------------------------------------------------------
// Pool global de materiales (toon + basic)
// ---------------------------------------------------------------------------

export interface ToonMatOpts {
  map?: Texture
  emissive?: ColorRepresentation
  emissiveIntensity?: number
  gradient?: readonly [string, string, string]
  transparent?: boolean
  opacity?: number
  /**
   * Rim light (fresnel) estilo Arcane: aclara el BORDE del personaje visto
   * desde la camara -> silueta luminosa que separa del fondo. `power` controla
   * el ancho del borde (mayor = mas fino), `intensity` la fuerza.
   */
  rim?: { color?: ColorRepresentation; power?: number; intensity?: number }
}

const toonPool = new Map<string, MeshToonMaterial>()
const basicPool = new Map<string, MeshBasicMaterial>()

function colorKey(value: ColorRepresentation | undefined): string {
  return value === undefined ? '' : new Color(value).getHexString()
}

/**
 * Inyecta un rim light fresnel en el fragment shader del MeshToonMaterial via
 * onBeforeCompile: `rim = pow(1 - dot(normal, viewDir), power)` sumado al
 * color final. Barato (sin pases extra) y funciona sobre SkinnedMesh.
 */
function applyRim(
  material: MeshToonMaterial,
  rim: NonNullable<ToonMatOpts['rim']>,
): void {
  const color = new Color(rim.color ?? '#ffffff')
  const power = rim.power ?? 3
  const intensity = rim.intensity ?? 0.6
  material.onBeforeCompile = (shader) => {
    shader.uniforms.rimColor = { value: color }
    shader.uniforms.rimPower = { value: power }
    shader.uniforms.rimIntensity = { value: intensity }
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        '#include <common>\nuniform vec3 rimColor;\nuniform float rimPower;\nuniform float rimIntensity;',
      )
      .replace(
        '#include <dithering_fragment>',
        'float rimF = pow(1.0 - clamp(dot(normalize(vNormal), normalize(vViewPosition)), 0.0, 1.0), rimPower);\n' +
          'gl_FragColor.rgb += rimColor * rimF * rimIntensity;\n' +
          '#include <dithering_fragment>',
      )
  }
}

function buildToon(
  color: ColorRepresentation,
  opts: ToonMatOpts,
): MeshToonMaterial {
  const material = new MeshToonMaterial({
    color,
    gradientMap: makeToonGradient(opts.gradient ?? DEFAULT_GRADIENT),
  })
  if (opts.map) {
    material.map = opts.map
  }
  if (opts.emissive !== undefined) {
    material.emissive = new Color(opts.emissive)
    material.emissiveIntensity = opts.emissiveIntensity ?? 1
  }
  if (opts.transparent) {
    material.transparent = true
    material.opacity = opts.opacity ?? 1
  }
  if (opts.rim) {
    applyRim(material, opts.rim)
  }
  return material
}

/**
 * @function toonMat
 * @description MeshToonMaterial del POOL global, cacheado por key
 *   (color+map+emissive+gradiente). `userData.shared = true` -> disposeDeep
 *   NUNCA lo libera. NO mutarlo (es compartido): para animar emissive usar
 *   `toonMatOwn`.
 */
export function toonMat(
  color: ColorRepresentation,
  opts: ToonMatOpts = {},
): MeshToonMaterial {
  const key = [
    colorKey(color),
    opts.map?.uuid ?? '',
    colorKey(opts.emissive),
    opts.emissiveIntensity ?? '',
    (opts.gradient ?? DEFAULT_GRADIENT).join(','),
    opts.transparent ? `t${opts.opacity ?? 1}` : '',
    opts.rim
      ? `rim${colorKey(opts.rim.color)}:${opts.rim.power ?? 3}:${opts.rim.intensity ?? 0.6}`
      : '',
  ].join('|')
  const cached = toonPool.get(key)
  if (cached) {
    return cached
  }
  const material = buildToon(color, opts)
  material.userData.shared = true
  toonPool.set(key, material)
  return material
}

/**
 * @function toonMatOwn
 * @description Variante NO pooleada para materiales que la sala anima
 *   (pulso de emissive, estados rojo->verde). Se libera con la sala.
 */
export function toonMatOwn(
  color: ColorRepresentation,
  opts: ToonMatOpts = {},
): MeshToonMaterial {
  return buildToon(color, opts)
}

/**
 * @function basicMat
 * @description MeshBasicMaterial del pool (emisivos planos: pantallas,
 *   acentos que no dependen de luz). Compartido — no mutar.
 */
export function basicMat(
  color: ColorRepresentation,
  opts: { transparent?: boolean; opacity?: number } = {},
): MeshBasicMaterial {
  const key = [
    colorKey(color),
    opts.transparent ? `t${opts.opacity ?? 1}` : '',
  ].join('|')
  const cached = basicPool.get(key)
  if (cached) {
    return cached
  }
  const material = new MeshBasicMaterial({ color })
  if (opts.transparent) {
    material.transparent = true
    material.opacity = opts.opacity ?? 1
  }
  material.userData.shared = true
  basicPool.set(key, material)
  return material
}

// ---------------------------------------------------------------------------
// Contornos — ELIMINADOS (pedido del dueno 2026-07-07)
// ---------------------------------------------------------------------------

/**
 * @function outlineGroup
 * @description NO-OP. Los contornos de tinta (inverted-hull) se eliminaron de
 *   TODAS las salas: el look pasa a 3D toon limpio, sin borde negro. Se
 *   conserva la firma vacia para no editar los ~13 archivos de sala que la
 *   llaman; la llamada simplemente no hace nada (y ahorra draw calls). Marcar
 *   `userData.noOutline` en un mesh ya no tiene efecto.
 */
export function outlineGroup(_root: Object3D, _thickness = 1.04): void {
  // sin contorno
}

// ---------------------------------------------------------------------------
// Texturas ink (canvas 512, deterministas, POOL por theme)
// ---------------------------------------------------------------------------

const inkTextureCache = new Map<string, CanvasTexture>()

/** Trazo "a mano": segmentos con jitter perpendicular. */
function wobblyLine(
  ctx: CanvasRenderingContext2D,
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  rng: () => number,
  jitter = 2,
): void {
  const steps = 12
  ctx.beginPath()
  ctx.moveTo(x0 + (rng() - 0.5) * jitter, y0 + (rng() - 0.5) * jitter)
  for (let i = 1; i <= steps; i += 1) {
    const t = i / steps
    ctx.lineTo(
      x0 + (x1 - x0) * t + (rng() - 0.5) * 2 * jitter,
      y0 + (y1 - y0) * t + (rng() - 0.5) * 2 * jitter,
    )
  }
  ctx.stroke()
}

/** Screentone: puntitos regulares (firma manga), muy sutil. */
function screentone(
  ctx: CanvasRenderingContext2D,
  size: number,
  ink: string,
  alpha: number,
): void {
  ctx.globalAlpha = alpha
  ctx.fillStyle = ink
  for (let y = 0; y < size; y += 8) {
    for (let x = (y / 8) % 2 === 0 ? 0 : 4; x < size; x += 8) {
      ctx.fillRect(x, y, 1.4, 1.4)
    }
  }
  ctx.globalAlpha = 1
}

/** Hatching diagonal de esquina — SOLO para pantallas/viñetas (en los
 *  muros se veia como "lineas sin sentido" en cada esquina y se elimino). */
function hatchCorner(
  ctx: CanvasRenderingContext2D,
  originX: number,
  direction: 1 | -1,
  rng: () => number,
): void {
  ctx.globalAlpha = 0.3
  ctx.lineWidth = 3
  const count = 6 + Math.floor(rng() * 4)
  for (let i = 0; i < count; i += 1) {
    const offset = 14 + i * 12 + rng() * 5
    ctx.beginPath()
    ctx.moveTo(originX + direction * offset, 0)
    ctx.lineTo(originX, offset)
    ctx.stroke()
  }
  ctx.globalAlpha = 1
}

/**
 * @function inkWallTexture
 * @description Muro manga-ink: base plana + lineas horizontales wobbly +
 *   zocalo de trazo grueso (color `trim` del theme — el guiño morado del
 *   aula) + screentone sutil + AO fake leve. Sin hatching de esquinas.
 *   Cacheada por theme y COMPARTIDA (pool).
 */
export function inkWallTexture(theme: RoomTheme): CanvasTexture {
  const trim = theme.trim ?? theme.ink
  const key = `wall|${theme.wall}|${theme.ink}|${trim}`
  const cached = inkTextureCache.get(key)
  if (cached) {
    return cached
  }
  const rng = makeRng(hashSeed(key))
  const texture = makeCanvasTexture(512, (ctx, size) => {
    ctx.fillStyle = theme.wall
    ctx.fillRect(0, 0, size, size)
    ctx.strokeStyle = theme.ink
    ctx.lineCap = 'round'
    // lineas horizontales de trazo a mano
    for (const yRatio of [0.34, 0.6]) {
      ctx.globalAlpha = 0.4 + rng() * 0.15
      ctx.lineWidth = 3 + rng() * 2
      wobblyLine(ctx, 0, size * yRatio, size, size * yRatio, rng)
    }
    ctx.globalAlpha = 1
    // zocalo inferior: banda de trazo grueso irregular (trim)
    ctx.globalAlpha = 0.75
    ctx.fillStyle = trim
    ctx.fillRect(0, size - 14, size, 14)
    ctx.globalAlpha = 0.85
    ctx.strokeStyle = trim
    ctx.lineWidth = 5
    wobblyLine(ctx, 0, size - 16, size, size - 16, rng, 3)
    ctx.strokeStyle = theme.ink
    ctx.globalAlpha = 1
    screentone(ctx, size, theme.ink, 0.05)
    // AO fake sutil (el look plano manda): union techo + contacto piso
    const grad = ctx.createLinearGradient(0, 0, 0, size)
    grad.addColorStop(0, 'rgba(0,0,0,0.16)')
    grad.addColorStop(0.1, 'rgba(0,0,0,0)')
    grad.addColorStop(0.9, 'rgba(0,0,0,0)')
    grad.addColorStop(1, 'rgba(0,0,0,0.2)')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, size, size)
  })
  texture.userData.shared = true
  inkTextureCache.set(key, texture)
  return texture
}

/**
 * @function inkFloorTexture
 * @description Piso manga-ink: tablones/baldosas con lineas wobbly de tinta
 *   (no rectas perfectas) + trazos de desgaste. Cacheada y compartida.
 */
export function inkFloorTexture(theme: RoomTheme): CanvasTexture {
  const key = `floor|${theme.floor}|${theme.ink}`
  const cached = inkTextureCache.get(key)
  if (cached) {
    return cached
  }
  const rng = makeRng(hashSeed(key))
  const texture = makeCanvasTexture(512, (ctx, size) => {
    ctx.fillStyle = theme.floor
    ctx.fillRect(0, 0, size, size)
    ctx.strokeStyle = theme.ink
    ctx.lineCap = 'round'
    const rows = 4
    const step = size / rows
    // tablones horizontales
    ctx.globalAlpha = 0.5
    for (let i = 0; i <= rows; i += 1) {
      ctx.lineWidth = 3 + rng() * 1.5
      wobblyLine(ctx, 0, i * step, size, i * step, rng)
    }
    // juntas verticales alternadas
    for (let row = 0; row < rows; row += 1) {
      const jointX = ((row % 2 === 0 ? 0.33 : 0.66) + rng() * 0.1) * size
      ctx.lineWidth = 3
      wobblyLine(ctx, jointX, row * step, jointX, (row + 1) * step, rng)
    }
    // trazos sueltos de desgaste
    ctx.globalAlpha = 0.14
    for (let i = 0; i < 6; i += 1) {
      const x = rng() * size
      const y = rng() * size
      ctx.lineWidth = 2 + rng() * 2
      wobblyLine(ctx, x, y, x + 20 + rng() * 40, y + (rng() - 0.5) * 14, rng)
    }
    ctx.globalAlpha = 1
    screentone(ctx, size, theme.ink, 0.04)
  })
  texture.userData.shared = true
  inkTextureCache.set(key, texture)
  return texture
}

// ---------------------------------------------------------------------------
// Labels (lettering manga — reemplazo del Text SDF anterior)
// ---------------------------------------------------------------------------

export interface LabelOpts {
  /** Altura del texto en unidades de mundo (default 0.3). */
  size?: number
  /** Relleno del lettering (default papel claro). */
  color?: string
  /** Tinta del contorno grueso (default INK). */
  ink?: string
  font?: string
}

/**
 * @function label
 * @description Plane con canvas transparente: strokeText de tinta gruesa +
 *   fillText de color — lettering manga. NO compartida: se libera con la
 *   sala (disposeDeep).
 */
export function label(text: string, opts: LabelOpts = {}): Mesh {
  const size = opts.size ?? 0.3
  const height = 128
  let fontPx = 88
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('toon: canvas 2d context no disponible')
  }
  const family = opts.font ?? MANGA_FONT
  ctx.font = `bold ${fontPx}px ${family}`
  let width = Math.ceil(ctx.measureText(text).width) + 48
  // presupuesto AC-10: canvas <= 512 — texto largo baja el font, no sube px
  if (width > 512) {
    fontPx = Math.floor((fontPx * 512) / width)
    width = 512
  }
  canvas.width = width
  canvas.height = height
  ctx.font = `bold ${fontPx}px ${family}`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.lineJoin = 'round'
  ctx.lineWidth = Math.max(5, Math.round(fontPx * 0.09))
  ctx.strokeStyle = opts.ink ?? INK
  ctx.strokeText(text, width / 2, height / 2)
  ctx.fillStyle = opts.color ?? '#f5f2e8'
  ctx.fillText(text, width / 2, height / 2)
  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  texture.anisotropy = anisotropy
  const material = new MeshBasicMaterial({ map: texture, transparent: true })
  const mesh = new Mesh(
    new PlaneGeometry((size * width) / height, size),
    material,
  )
  mesh.userData.noOutline = true
  return mesh
}

// ---------------------------------------------------------------------------
// ScreenPanel (viñeta manga con texto monospace)
// ---------------------------------------------------------------------------

export interface ScreenPanelOpts {
  lines: readonly string[]
  title?: string
  theme: Pick<RoomTheme, 'screenBg' | 'screenFg' | 'ink'>
  width: number
  height: number
  /** LED de estado abajo a la derecha (pantallas apagadas/encendidas). */
  dot?: string
  /**
   * Estilo de la pantalla. Por defecto `terminal` (viñeta manga con texto
   * monospace). `windows7` / `windowsxp` dibujan el escritorio retro de esa
   * era (wallpaper + taskbar + ventana) — para las PCs de las salas viejas.
   */
  kind?: 'terminal' | 'windows7' | 'windowsxp'
}

/**
 * Escritorio retro (Windows 7 / XP) dibujado con Canvas 2D — cero asset,
 * nítido a cualquier zoom. Windows 7: wallpaper azul degradado, taskbar
 * translúcida oscura con orbe Start y ventana Aero. XP: wallpaper "Bliss"
 * (cielo + colina verde), taskbar azul con botón Start verde. Las `lines`
 * del CV se muestran como el contenido de la ventana (sigue siendo texto real
 * del showcase). El titulo va en la barra de la ventana.
 */
function windowsDesktopTexture(
  opts: ScreenPanelOpts & { xp: boolean },
): CanvasTexture {
  return makeCanvasTexture(512, (ctx, size) => {
    const bar = Math.round(size * 0.085) // alto de la taskbar
    // ---- wallpaper ----
    if (opts.xp) {
      // Bliss: cielo celeste degradado + colina verde
      const sky = ctx.createLinearGradient(0, 0, 0, size * 0.62)
      sky.addColorStop(0, '#3a6ea5')
      sky.addColorStop(0.55, '#8fc0ea')
      sky.addColorStop(1, '#cfe6f7')
      ctx.fillStyle = sky
      ctx.fillRect(0, 0, size, size)
      ctx.fillStyle = '#7aa84b'
      ctx.beginPath()
      ctx.moveTo(0, size * 0.66)
      ctx.quadraticCurveTo(size * 0.4, size * 0.5, size, size * 0.6)
      ctx.lineTo(size, size)
      ctx.lineTo(0, size)
      ctx.closePath()
      ctx.fill()
      ctx.fillStyle = '#6b9a3f'
      ctx.beginPath()
      ctx.moveTo(0, size * 0.74)
      ctx.quadraticCurveTo(size * 0.55, size * 0.62, size, size * 0.72)
      ctx.lineTo(size, size)
      ctx.lineTo(0, size)
      ctx.closePath()
      ctx.fill()
    } else {
      // Windows 7: degradado azul profundo con halo central
      const bg = ctx.createRadialGradient(
        size / 2,
        size * 0.42,
        size * 0.1,
        size / 2,
        size * 0.42,
        size * 0.75,
      )
      bg.addColorStop(0, '#2b6bb0')
      bg.addColorStop(0.6, '#164a86')
      bg.addColorStop(1, '#0a2b52')
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, size, size)
    }
    // ---- ventana Aero/Luna ----
    const wx = size * 0.14
    const wy = size * 0.16
    const ww = size * 0.72
    const wh = size * 0.58
    const titleH = size * 0.07
    // sombra
    ctx.fillStyle = 'rgba(0,0,0,0.28)'
    ctx.fillRect(wx + 4, wy + 5, ww, wh)
    // marco ventana
    ctx.fillStyle = opts.xp ? '#ece9d8' : '#f2f6fb'
    ctx.fillRect(wx, wy, ww, wh)
    // barra de titulo
    const tg = ctx.createLinearGradient(0, wy, 0, wy + titleH)
    if (opts.xp) {
      tg.addColorStop(0, '#3f8be8')
      tg.addColorStop(1, '#0a4bc0')
    } else {
      tg.addColorStop(0, '#dbe9f7')
      tg.addColorStop(1, '#a9c9ec')
    }
    ctx.fillStyle = tg
    ctx.fillRect(wx, wy, ww, titleH)
    // titulo de la ventana
    ctx.fillStyle = opts.xp ? '#ffffff' : '#1c3c60'
    ctx.font = `bold 22px ${MONO_FONT}`
    ctx.fillText(
      (opts.title ?? 'ventana').slice(0, 24),
      wx + 14,
      wy + titleH * 0.7,
    )
    // botones de ventana (min/max/close)
    const bs = titleH * 0.5
    const by = wy + (titleH - bs) / 2
    ctx.fillStyle = opts.xp ? '#e24b3a' : '#d64a3f'
    ctx.fillRect(wx + ww - bs - 8, by, bs, bs)
    ctx.fillStyle = opts.xp ? '#f0f0f0' : '#c6d8ee'
    ctx.fillRect(wx + ww - bs * 2 - 16, by, bs, bs)
    ctx.fillRect(wx + ww - bs * 3 - 24, by, bs, bs)
    // contenido de la ventana: las lineas del CV
    ctx.fillStyle = '#1a1c22'
    ctx.font = `20px ${MONO_FONT}`
    let y = wy + titleH + 34
    for (const line of opts.lines.slice(0, 10)) {
      ctx.fillText(line.slice(0, 30), wx + 16, y)
      y += 30
    }
    // ---- taskbar ----
    if (opts.xp) {
      const tb = ctx.createLinearGradient(0, size - bar, 0, size)
      tb.addColorStop(0, '#3f8be8')
      tb.addColorStop(1, '#245bc4')
      ctx.fillStyle = tb
      ctx.fillRect(0, size - bar, size, bar)
      // boton Start verde
      ctx.fillStyle = '#3fa63f'
      ctx.beginPath()
      const sbW = size * 0.2
      ctx.roundRect(0, size - bar + 3, sbW, bar - 6, bar * 0.4)
      ctx.fill()
      ctx.fillStyle = '#ffffff'
      ctx.font = `italic bold 24px ${MONO_FONT}`
      ctx.fillText('start', 20, size - bar * 0.32)
    } else {
      ctx.fillStyle = 'rgba(20,28,44,0.82)'
      ctx.fillRect(0, size - bar, size, bar)
      // orbe Start (circulo con glow)
      const ox = bar * 0.55
      const oy = size - bar / 2
      const orb = ctx.createRadialGradient(ox, oy, 2, ox, oy, bar * 0.42)
      orb.addColorStop(0, '#cfe6ff')
      orb.addColorStop(0.5, '#3a8fd8')
      orb.addColorStop(1, '#12406e')
      ctx.fillStyle = orb
      ctx.beginPath()
      ctx.arc(ox, oy, bar * 0.4, 0, Math.PI * 2)
      ctx.fill()
      // iconos pinneados (cuadraditos)
      ctx.fillStyle = 'rgba(255,255,255,0.18)'
      for (let i = 0; i < 3; i += 1) {
        ctx.fillRect(
          bar * 1.25 + i * bar * 0.85,
          size - bar * 0.78,
          bar * 0.55,
          bar * 0.55,
        )
      }
    }
    // reloj
    ctx.fillStyle = '#ffffff'
    ctx.font = `18px ${MONO_FONT}`
    ctx.fillText('09:41', size - 62, size - bar * 0.32)
  })
}

/**
 * @function screenTexture
 * @description Textura de pantalla/viñeta manga: marco de tinta irregular
 *   con hatching + texto monospace + LED opcional. Base de screenPanel y
 *   de las pantallas intercambiables (PC que bootea, OFFLINE->ONLINE).
 *   `kind: 'windows7' | 'windowsxp'` dibuja el escritorio retro de esa era.
 */
export function screenTexture(opts: ScreenPanelOpts): CanvasTexture {
  if (opts.kind === 'windows7' || opts.kind === 'windowsxp') {
    return windowsDesktopTexture({ ...opts, xp: opts.kind === 'windowsxp' })
  }
  const rng = makeRng(hashSeed([opts.title ?? '', ...opts.lines].join('|')))
  return makeCanvasTexture(512, (ctx, size) => {
    ctx.fillStyle = opts.theme.screenBg
    ctx.fillRect(0, 0, size, size)
    // marco de viñeta: doble trazo wobbly
    ctx.strokeStyle = opts.theme.ink
    ctx.lineCap = 'round'
    ctx.globalAlpha = 0.95
    ctx.lineWidth = 7
    wobblyLine(ctx, 8, 10, size - 8, 10, rng, 2.5)
    wobblyLine(ctx, size - 10, 8, size - 10, size - 8, rng, 2.5)
    wobblyLine(ctx, size - 8, size - 10, 8, size - 10, rng, 2.5)
    wobblyLine(ctx, 10, size - 8, 10, 8, rng, 2.5)
    ctx.globalAlpha = 0.4
    ctx.lineWidth = 3
    wobblyLine(ctx, 20, 22, size - 20, 22, rng, 2)
    // hatching de esquina (firma de viñeta)
    ctx.strokeStyle = opts.theme.screenFg
    hatchCorner(ctx, size, -1, rng)
    ctx.globalAlpha = 1
    // contenido
    ctx.fillStyle = opts.theme.screenFg
    let y = 72
    if (opts.title) {
      ctx.font = `bold 34px ${MONO_FONT}`
      ctx.fillText(opts.title, 28, y)
      y += 52
    }
    ctx.font = `24px ${MONO_FONT}`
    for (const line of opts.lines.slice(0, 12)) {
      ctx.fillText(line.slice(0, 34), 28, y)
      y += 36
    }
    if (opts.dot) {
      ctx.fillStyle = opts.dot
      ctx.beginPath()
      ctx.arc(size - 34, size - 34, 9, 0, Math.PI * 2)
      ctx.fill()
    }
  })
}

/**
 * @function screenPanel
 * @description Pantalla/pizarra como viñeta manga sobre un plane.
 *   MeshBasicMaterial (plano emisivo: no depende de luz). NO compartido:
 *   se libera con la sala.
 */
export function screenPanel(opts: ScreenPanelOpts): Mesh {
  const material = new MeshBasicMaterial({ map: screenTexture(opts) })
  const mesh = new Mesh(new PlaneGeometry(opts.width, opts.height), material)
  mesh.userData.noOutline = true
  return mesh
}

// ---------------------------------------------------------------------------
// Geometrias unitarias compartidas
// ---------------------------------------------------------------------------

interface UnitGeometries {
  box: BoxGeometry
  sphere: SphereGeometry
  cylinder: CylinderGeometry
  plane: PlaneGeometry
  /** Cuerpos chibi redondeados (una talla, compartida por TODOS). */
  capsuleTorso: CapsuleGeometry
  capsuleLeg: CapsuleGeometry
  capsuleArm: CapsuleGeometry
}

let units: UnitGeometries | null = null

/** Geometrias 1x1 compartidas: mesh escalado = cero allocs por prop. */
export function unitGeo(): UnitGeometries {
  if (!units) {
    units = {
      box: new BoxGeometry(1, 1, 1),
      sphere: new SphereGeometry(0.5, 16, 12),
      cylinder: new CylinderGeometry(0.5, 0.5, 1, 12),
      plane: new PlaneGeometry(1, 1),
      capsuleTorso: new CapsuleGeometry(0.16, 0.18, 4, 12),
      capsuleLeg: new CapsuleGeometry(0.07, 0.36, 4, 10),
      capsuleArm: new CapsuleGeometry(0.055, 0.28, 4, 10),
    }
    for (const geometry of Object.values(units)) {
      geometry.userData.shared = true
    }
  }
  return units
}

/** Box del pool escalada (w, h, d). El hull hereda la escala. */
export function boxMesh(
  w: number,
  h: number,
  d: number,
  material: MeshToonMaterial | MeshBasicMaterial,
): Mesh {
  const mesh = new Mesh(unitGeo().box, material)
  mesh.scale.set(w, h, d)
  return mesh
}

export interface BoxSpec {
  w: number
  h: number
  d: number
  x: number
  y: number
  z: number
  rotY?: number
}

/**
 * @function mergedBoxes
 * @description N cajas estaticas del mismo material fusionadas en UNA
 *   geometry (1 draw call). Palanca principal del presupuesto AC-10:
 *   muros de shell, escritorios, sillas, jambas. La geometry resultante
 *   es propia (disposeDeep la libera).
 */
export function mergedBoxes(
  parts: readonly BoxSpec[],
  material: MeshToonMaterial | MeshBasicMaterial,
): Mesh {
  const geos = parts.map((p) => {
    const geo = new BoxGeometry(p.w, p.h, p.d)
    if (p.rotY) {
      geo.rotateY(p.rotY)
    }
    geo.translate(p.x, p.y, p.z)
    return geo
  })
  const merged = mergeGeometries(geos)
  for (const geo of geos) {
    geo.dispose()
  }
  return new Mesh(merged, material)
}

/**
 * @function outlinedMergedBoxes
 * @description mergedBoxes SIN contorno (los contornos se eliminaron). Devuelve
 *   solo el fill envuelto en un `Group` para conservar el tipo de retorno que
 *   esperan las salas. `opts.inflate` queda ignorado.
 */
export function outlinedMergedBoxes(
  parts: readonly BoxSpec[],
  material: MeshToonMaterial | MeshBasicMaterial,
  opts: { inflate?: number; castShadow?: boolean } = {},
): Group {
  const group = new Group()
  const fill = mergedBoxes(parts, material)
  if (opts.castShadow) {
    fill.castShadow = true
  }
  group.add(fill)
  return group
}

// ---------------------------------------------------------------------------
// Dispose
// ---------------------------------------------------------------------------

/**
 * @function disposeDeep
 * @description Libera geometrias, materiales y texturas de TODO el arbol,
 *   SALVO lo marcado `userData.shared === true` (pool toon, gradientes,
 *   texturas ink por theme, geometrias unitarias). Es la regla de memoria
 *   del zone manager (AC-3).
 */
export function disposeDeep(root: Object3D): void {
  root.traverse((obj) => {
    if (!(obj instanceof Mesh)) {
      return
    }
    if (obj.geometry.userData.shared !== true) {
      obj.geometry.dispose()
    }
    const materials = Array.isArray(obj.material)
      ? obj.material
      : [obj.material]
    for (const material of materials) {
      disposeOwnMaterial(material)
    }
  })
}

/** Libera un material propio + sus texturas (skip si es del pool). */
function disposeOwnMaterial(material: Material): void {
  if (material.userData.shared === true) {
    return
  }
  for (const value of Object.values(material)) {
    if (value instanceof Texture && value.userData.shared !== true) {
      value.dispose()
    }
  }
  material.dispose()
}

/** Teardown TOTAL del pool (solo al salir de la experiencia). */
export function disposeToonPool(): void {
  for (const texture of gradientCache.values()) {
    texture.dispose()
  }
  gradientCache.clear()
  for (const texture of inkTextureCache.values()) {
    texture.dispose()
  }
  inkTextureCache.clear()
  for (const material of toonPool.values()) {
    material.dispose()
  }
  toonPool.clear()
  for (const material of basicPool.values()) {
    material.dispose()
  }
  basicPool.clear()
  if (units) {
    for (const geometry of Object.values(units)) {
      geometry.dispose()
    }
    units = null
  }
}
