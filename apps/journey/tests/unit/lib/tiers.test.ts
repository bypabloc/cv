import { describe, expect, it } from 'vitest'
import { readTierEnv, resolveTier, type TierEnv } from '../../../src/lib/tiers'

function makeEnv(overrides: Partial<TierEnv>): TierEnv {
  return {
    webgl2: true,
    reducedMotion: false,
    isMobile: false,
    deviceMemory: undefined,
    ...overrides,
  }
}

describe('resolveTier', () => {
  it('Given un browser sin WebGL2 When se resuelve el tier Then es static', () => {
    expect(resolveTier(makeEnv({ webgl2: false }))).toBe('static')
  })

  it('Given prefers-reduced-motion When se resuelve el tier Then es static', () => {
    expect(resolveTier(makeEnv({ reducedMotion: true }))).toBe('static')
  })

  it('Given deviceMemory de 1GB When se resuelve el tier Then es static (HW debil)', () => {
    expect(resolveTier(makeEnv({ deviceMemory: 1 }))).toBe('static')
  })

  it('Given un movil con WebGL2 When se resuelve el tier Then es reduced', () => {
    expect(resolveTier(makeEnv({ isMobile: true, deviceMemory: 6 }))).toBe(
      'reduced',
    )
  })

  it('Given un desktop con 3GB When se resuelve el tier Then es reduced', () => {
    expect(resolveTier(makeEnv({ deviceMemory: 3 }))).toBe('reduced')
  })

  it('Given un desktop con 8GB When se resuelve el tier Then es full', () => {
    expect(resolveTier(makeEnv({ deviceMemory: 8 }))).toBe('full')
  })

  it('Given un desktop sin deviceMemory reportada When se resuelve el tier Then es full (API no soportada != HW debil)', () => {
    expect(resolveTier(makeEnv({}))).toBe('full')
  })
})

describe('readTierEnv', () => {
  it('Given un probe de desktop Chrome When se lee el env Then no es movil ni reduced-motion', () => {
    const env = readTierEnv({
      webgl2: true,
      matchMedia: () => ({ matches: false }),
      userAgent:
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0',
      maxTouchPoints: 0,
      deviceMemory: 8,
    })

    expect(env).toEqual({
      webgl2: true,
      reducedMotion: false,
      isMobile: false,
      deviceMemory: 8,
    })
  })

  it('Given un probe de iPhone When se lee el env Then es movil por user agent', () => {
    const env = readTierEnv({
      webgl2: true,
      matchMedia: () => ({ matches: false }),
      userAgent:
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1',
      maxTouchPoints: 5,
    })

    expect(env.isMobile).toBe(true)
    expect(env.deviceMemory).toBe(undefined)
  })

  it('Given un probe con pointer coarse y multitouch When se lee el env Then es movil aunque el UA no matchee', () => {
    const env = readTierEnv({
      webgl2: true,
      matchMedia: (query: string) => ({
        matches: query === '(pointer: coarse)',
      }),
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64)',
      maxTouchPoints: 5,
    })

    expect(env.isMobile).toBe(true)
  })

  it('Given un probe con prefers-reduced-motion When se lee el env Then reducedMotion es true', () => {
    const env = readTierEnv({
      webgl2: true,
      matchMedia: (query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
      }),
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64)',
      maxTouchPoints: 0,
    })

    expect(env.reducedMotion).toBe(true)
  })

  it('Given un probe sin matchMedia When se lee el env Then degrada sin reduced-motion ni coarse', () => {
    const env = readTierEnv({
      webgl2: false,
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64)',
      maxTouchPoints: 0,
    })

    expect(env).toEqual({
      webgl2: false,
      reducedMotion: false,
      isMobile: false,
      deviceMemory: undefined,
    })
  })
})
