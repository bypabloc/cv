/**
 * @module toon (engine)
 * @description Base visual manga-ink del motor vanilla: pool GLOBAL de
 *   MeshToonMaterial (compartir material = menos state changes y shaders
 *   compilados 1 sola vez), gradientes de 3 escalones duros, contornos
 *   inverted hull, texturas canvas de tinta deterministas (LCG), labels
 *   con lettering manga (reemplazan al Text SDF anterior) y disposeDeep con
 *   guard `userData.shared` para nunca liberar el pool.
 *
 *   Nota DS: los hex son colores de MATERIAL WebGL/canvas, no CSS del UI.
 */
import {
  BackSide,
  BoxGeometry,
  CanvasTexture,
  Color,
  type ColorRepresentation,
  CylinderGeometry,
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

type DrawFn = (ctx: CanvasRenderingContext2D, size: number) => void

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
}

const toonPool = new Map<string, MeshToonMaterial>()
const basicPool = new Map<string, MeshBasicMaterial>()

function colorKey(value: ColorRepresentation | undefined): string {
  return value === undefined ? '' : new Color(value).getHexString()
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
// Contornos inverted hull
// ---------------------------------------------------------------------------

let outlineSingleton: MeshBasicMaterial | null = null

function outlineMaterial(): MeshBasicMaterial {
  if (!outlineSingleton) {
    outlineSingleton = new MeshBasicMaterial({ color: INK, side: BackSide })
    outlineSingleton.userData.shared = true
  }
  return outlineSingleton
}

/**
 * @function addOutline
 * @description Contorno de tinta: clon del mesh escalado ~1.04 con material
 *   negro BackSide COMPARTIDO. Reusa la MISMA geometry (cero costo extra de
 *   memoria). Los muros interiores NO llevan hull (se ve del reves): sus
 *   lineas van dibujadas en la textura.
 */
export function addOutline(mesh: Mesh, thickness = 1.04): Mesh {
  const hull = new Mesh(mesh.geometry, outlineMaterial())
  hull.scale.setScalar(thickness)
  hull.userData.outline = true
  mesh.add(hull)
  return hull
}

/**
 * Aplica hull a todos los meshes del arbol salvo `userData.noOutline`
 * (que corta el subtree completo) y los que ya tienen su hull.
 */
export function outlineGroup(root: Object3D, thickness = 1.04): void {
  const targets: Mesh[] = []
  collectOutlineTargets(root, targets)
  for (const mesh of targets) {
    addOutline(mesh, thickness)
  }
}

function collectOutlineTargets(obj: Object3D, out: Mesh[]): void {
  if (obj.userData.noOutline === true || obj.userData.outline === true) {
    return
  }
  if (
    obj instanceof Mesh &&
    !obj.children.some((child) => child.userData.outline === true)
  ) {
    out.push(obj)
  }
  for (const child of obj.children) {
    collectOutlineTargets(child, out)
  }
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
 *   hatching en esquinas superiores + zocalo de trazo grueso + screentone
 *   sutil + AO fake leve. Cacheada por theme y COMPARTIDA (pool).
 */
export function inkWallTexture(theme: RoomTheme): CanvasTexture {
  const key = `wall|${theme.wall}|${theme.ink}`
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
    // hatching diagonal corto en las 2 esquinas superiores
    hatchCorner(ctx, 0, 1, rng)
    hatchCorner(ctx, size, -1, rng)
    // zocalo inferior: banda de trazo grueso irregular
    ctx.globalAlpha = 0.55
    ctx.fillStyle = theme.ink
    ctx.fillRect(0, size - 14, size, 14)
    ctx.globalAlpha = 0.8
    ctx.lineWidth = 5
    wobblyLine(ctx, 0, size - 16, size, size - 16, rng, 3)
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
}

/**
 * @function screenPanel
 * @description Pantalla/pizarra como viñeta manga: marco de tinta irregular
 *   con hatching en 2 esquinas + texto monospace. MeshBasicMaterial (plano
 *   emisivo: no depende de luz). NO compartido: se libera con la sala.
 */
export function screenPanel(opts: ScreenPanelOpts): Mesh {
  const rng = makeRng(hashSeed([opts.title ?? '', ...opts.lines].join('|')))
  const texture = makeCanvasTexture(512, (ctx, size) => {
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
  })
  const material = new MeshBasicMaterial({ map: texture })
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
  if (outlineSingleton) {
    outlineSingleton.dispose()
    outlineSingleton = null
  }
  if (units) {
    for (const geometry of Object.values(units)) {
      geometry.dispose()
    }
    units = null
  }
}
