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

// three clampa la anisotropia al maximo del GPU (Math.min interno): pedir 16
// equivale a maxAnisotropy en desktop y elimina el blur/pixelado en angulos
// rasantes (pisos y paredes vistos de costado en el walking-sim).
const ANISOTROPY = 16

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
  texture.anisotropy = ANISOTROPY
  return texture
}

/**
 * Yeso/estuco: base + manchas de baja frecuencia (rompen lo plano) + motas
 * finas de ruido. Las manchas se alejan de los bordes para que la textura
 * siga tileando sin costuras visibles. Con `ao` agrega el gradiente oscuro
 * arriba (union con techo) y abajo (zocalo) — AO fake sin post-processing;
 * exige repeat vertical = 1 para mapear piso->techo.
 */
export function plasterTexture(
  base: string,
  speck: string,
  seed = 7,
  ao = false,
): CanvasTexture {
  return makeCanvasTexture(512, (ctx, size) => {
    ctx.fillStyle = base
    ctx.fillRect(0, 0, size, size)
    const rng = makeRng(seed)
    for (let i = 0; i < 24; i += 1) {
      const radius = 40 + rng() * 90
      const x = radius + rng() * (size - radius * 2)
      const y = radius + rng() * (size - radius * 2)
      const blotch = ctx.createRadialGradient(x, y, 0, x, y, radius)
      const tone = rng() > 0.5 ? '255,255,255' : '0,0,0'
      blotch.addColorStop(0, `rgba(${tone},0.05)`)
      blotch.addColorStop(1, `rgba(${tone},0)`)
      ctx.fillStyle = blotch
      ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2)
    }
    ctx.fillStyle = speck
    for (let i = 0; i < 3400; i += 1) {
      ctx.globalAlpha = 0.03 + rng() * 0.07
      ctx.fillRect(rng() * size, rng() * size, 1.5, 1.5)
    }
    ctx.globalAlpha = 1
    if (ao) {
      const grad = ctx.createLinearGradient(0, 0, 0, size)
      grad.addColorStop(0, 'rgba(0,0,0,0.34)')
      grad.addColorStop(0.14, 'rgba(0,0,0,0)')
      grad.addColorStop(0.86, 'rgba(0,0,0,0)')
      grad.addColorStop(1, 'rgba(0,0,0,0.42)')
      ctx.fillStyle = grad
      ctx.fillRect(0, 0, size, size)
      // zocalo: franja mas oscura de contacto con el piso
      ctx.globalAlpha = 0.35
      ctx.fillStyle = '#000000'
      ctx.fillRect(0, size - 14, size, 14)
      ctx.globalAlpha = 1
    }
  })
}

/**
 * Piso de baldosas: variacion de tono + desgaste + bisel (luz arriba/
 * izquierda, sombra abajo/derecha) por baldosa, y junta de grout.
 */
export function tileTexture(
  base: string,
  line: string,
  tiles = 4,
  seed = 11,
): CanvasTexture {
  return makeCanvasTexture(512, (ctx, size) => {
    ctx.fillStyle = base
    ctx.fillRect(0, 0, size, size)
    const rng = makeRng(seed)
    const step = size / tiles
    for (let ix = 0; ix < tiles; ix += 1) {
      for (let iz = 0; iz < tiles; iz += 1) {
        const x = ix * step
        const y = iz * step
        ctx.globalAlpha = rng() * 0.07
        ctx.fillStyle = rng() > 0.35 ? '#ffffff' : '#000000'
        ctx.fillRect(x, y, step, step)
        // mancha de desgaste puntual
        ctx.globalAlpha = 0.05
        ctx.fillStyle = '#000000'
        ctx.fillRect(
          x + rng() * step * 0.6,
          y + rng() * step * 0.6,
          step * 0.3,
          step * 0.2,
        )
        // bisel fake (vende el relieve sin normal map)
        ctx.globalAlpha = 0.1
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(x, y, step, 2)
        ctx.fillRect(x, y, 2, step)
        ctx.fillStyle = '#000000'
        ctx.fillRect(x, y + step - 2, step, 2)
        ctx.fillRect(x + step - 2, y, 2, step)
      }
    }
    ctx.globalAlpha = 1
    ctx.strokeStyle = line
    ctx.lineWidth = 3
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
