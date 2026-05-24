/**
 * @description Tests para validateApiEndpoint y validateTurnstileSitekey.
 *   Cubre los 4 escenarios del guard (vacio, mismatch, match, sin
 *   BASE_DOMAIN) y mapea 1:1 a los AC del plan build-env-vars-per-env.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  validateApiEndpoint,
  validateTurnstileSitekey,
} from '../../../src/lib/validate-build-env'

describe('validateApiEndpoint', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('Given undefined When validate Then throws con mensaje claro [Capa A]', () => {
    expect(() => validateApiEndpoint(undefined)).toThrow(
      /PUBLIC_API_ENDPOINT vacio/,
    )
  })

  it('Given empty string When validate Then throws con mensaje claro [Capa A]', () => {
    expect(() => validateApiEndpoint('')).toThrow(/PUBLIC_API_ENDPOINT vacio/)
  })

  it('Given BASE_DOMAIN=dev y endpoint que matchea When validate Then retorna el valor', () => {
    vi.stubEnv('BASE_DOMAIN', 'portfolio.dev.the-full-stack.com')
    const endpoint = 'https://api.portfolio.dev.the-full-stack.com'
    expect(validateApiEndpoint(endpoint)).toBe(endpoint)
  })

  it('Given BASE_DOMAIN=dev y endpoint apunta a prod When validate Then throws con ambos valores [Capa A]', () => {
    vi.stubEnv('BASE_DOMAIN', 'portfolio.dev.the-full-stack.com')
    const wrong = 'https://api.portfolio.the-full-stack.com'
    expect(() => validateApiEndpoint(wrong)).toThrow(
      /no matchea BASE_DOMAIN.*portfolio\.dev/,
    )
  })

  it('Given BASE_DOMAIN ausente When validate con cualquier URL no vacia Then retorna el valor (modo local)', () => {
    vi.stubEnv('BASE_DOMAIN', '')
    const endpoint = 'https://api.example.test'
    expect(validateApiEndpoint(endpoint)).toBe(endpoint)
  })

  it('Given BASE_DOMAIN=prod y endpoint prod matcheado When validate Then retorna el valor', () => {
    vi.stubEnv('BASE_DOMAIN', 'portfolio.the-full-stack.com')
    const endpoint = 'https://api.portfolio.the-full-stack.com'
    expect(validateApiEndpoint(endpoint)).toBe(endpoint)
  })
})

describe('validateTurnstileSitekey', () => {
  it('Given undefined When validate Then throws con mensaje claro', () => {
    expect(() => validateTurnstileSitekey(undefined)).toThrow(
      /PUBLIC_TURNSTILE_SITEKEY vacio/,
    )
  })

  it('Given empty string When validate Then throws', () => {
    expect(() => validateTurnstileSitekey('')).toThrow(
      /PUBLIC_TURNSTILE_SITEKEY vacio/,
    )
  })

  it('Given sitekey valido When validate Then retorna el valor', () => {
    const sitekey = '0x4AAAAAADPSoiQA_-LcRafo'
    expect(validateTurnstileSitekey(sitekey)).toBe(sitekey)
  })
})
