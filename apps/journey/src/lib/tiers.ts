/**
 * @module tiers
 * @description Sistema de 3 tiers del journey (arquitectura comun del plan):
 *   Full (desktop GPU) / Reduced (movil con WebGL -> tour guiado) / Static
 *   (sin WebGL, HW debil o prefers-reduced-motion -> CV 2D del HTML).
 *
 *   Logica PURA e inyectable: el glue de browser (canvas WebGL2, matchMedia
 *   reales) vive en la isla `Journey3D.tsx`, no aqui — asi el tier es 100%
 *   testeable en node.
 *
 * @see docs/specs/journey-3d-cv/04-arquitectura-comun.md
 */

export type Tier = 'full' | 'reduced' | 'static'

export interface TierEnv {
  webgl2: boolean
  reducedMotion: boolean
  isMobile: boolean
  /** GB reportados por `navigator.deviceMemory`; undefined si la API no existe. */
  deviceMemory?: number
}

/** Debajo de esto el HW no aguanta ni la escena reducida -> Static. */
export const STATIC_MEMORY_CEILING_GB = 2
/** Debajo de esto un desktop corre la escena simplificada -> Reduced. */
export const REDUCED_MEMORY_CEILING_GB = 4

/**
 * @function resolveTier
 * @description Decide el tier a partir de un TierEnv ya medido.
 *
 * @example
 *   resolveTier({ webgl2: false, reducedMotion: false, isMobile: false })
 *   // 'static'
 */
export function resolveTier(env: TierEnv): Tier {
  if (!env.webgl2 || env.reducedMotion) {
    return 'static'
  }
  if (
    env.deviceMemory !== undefined &&
    env.deviceMemory < STATIC_MEMORY_CEILING_GB
  ) {
    return 'static'
  }
  if (env.isMobile) {
    return 'reduced'
  }
  if (
    env.deviceMemory !== undefined &&
    env.deviceMemory < REDUCED_MEMORY_CEILING_GB
  ) {
    return 'reduced'
  }
  return 'full'
}

/** Piezas del browser que la deteccion necesita, inyectables en tests. */
export interface TierProbe {
  webgl2: boolean
  matchMedia?: (query: string) => { matches: boolean }
  userAgent?: string
  maxTouchPoints?: number
  deviceMemory?: number
}

const MOBILE_UA = /Mobi|Android|iPhone|iPad/i

/**
 * @function readTierEnv
 * @description Normaliza un probe del browser a TierEnv.
 *   Heuristica movil: UA movil, o pointer coarse + multitouch.
 */
export function readTierEnv(probe: TierProbe): TierEnv {
  const media = (query: string): boolean =>
    probe.matchMedia?.(query).matches ?? false
  const coarse = media('(pointer: coarse)')
  const uaMobile = MOBILE_UA.test(probe.userAgent ?? '')
  const isMobile = uaMobile || (coarse && (probe.maxTouchPoints ?? 0) > 1)
  return {
    webgl2: probe.webgl2,
    reducedMotion: media('(prefers-reduced-motion: reduce)'),
    isMobile,
    deviceMemory: probe.deviceMemory,
  }
}
