/**
 * @module textures
 * @description Texturas PROCEDURALES via Canvas API en runtime (enfoque
 *   Sidi Bou Said): cero archivos de textura, cero peso de red. Ruido
 *   determinista (LCG) para que cada build/carga pinte identico.
 *
 *   Nota DS: los hex de este modulo son colores de MATERIAL WebGL (se
 *   dibujan en canvas/three), no CSS del UI — los tokens var(--color-*)
 *   no aplican dentro del renderer.
 */
import { CanvasTexture, RepeatWrapping, SRGBColorSpace } from 'three'

type DrawFn = (ctx: CanvasRenderingContext2D, size: number) => void

/** LCG determinista (mulberry32) — no usa Math.random. */
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

export function makeCanvasTexture(size: number, draw: DrawFn): CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('textures: canvas 2d context no disponible')
  }
  draw(ctx, size)
  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  texture.wrapS = RepeatWrapping
  texture.wrapT = RepeatWrapping
  return texture
}

/** Yeso/estuco: base plana + motas sutiles de ruido. */
export function plasterTexture(
  base: string,
  speck: string,
  seed = 7,
): CanvasTexture {
  return makeCanvasTexture(256, (ctx, size) => {
    ctx.fillStyle = base
    ctx.fillRect(0, 0, size, size)
    const rng = makeRng(seed)
    ctx.fillStyle = speck
    for (let i = 0; i < 900; i += 1) {
      ctx.globalAlpha = 0.04 + rng() * 0.08
      ctx.fillRect(rng() * size, rng() * size, 1.5, 1.5)
    }
    ctx.globalAlpha = 1
  })
}

/** Piso de baldosas: grid de lineas sobre base. */
export function tileTexture(
  base: string,
  line: string,
  tiles = 4,
  seed = 11,
): CanvasTexture {
  return makeCanvasTexture(256, (ctx, size) => {
    ctx.fillStyle = base
    ctx.fillRect(0, 0, size, size)
    const rng = makeRng(seed)
    const step = size / tiles
    // variacion sutil por baldosa
    for (let ix = 0; ix < tiles; ix += 1) {
      for (let iz = 0; iz < tiles; iz += 1) {
        ctx.globalAlpha = rng() * 0.06
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(ix * step, iz * step, step, step)
      }
    }
    ctx.globalAlpha = 1
    ctx.strokeStyle = line
    ctx.lineWidth = 2
    for (let i = 0; i <= tiles; i += 1) {
      ctx.beginPath()
      ctx.moveTo(i * step, 0)
      ctx.lineTo(i * step, size)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(0, i * step)
      ctx.lineTo(size, i * step)
      ctx.stroke()
    }
  })
}
