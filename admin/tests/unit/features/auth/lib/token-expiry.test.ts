import { makeJwt, nowSec } from '@tests/mocks/jwt'
import { describe, expect, it } from 'vitest'
import { getJwtExpiry, isJwtExpired } from '@/features/auth/lib/token-expiry'

/**
 * @module tests/unit/features/auth/lib/token-expiry
 * @description Verifica la lectura del exp de un JWT.
 */
describe('getJwtExpiry', () => {
  it('Given un JWT con exp When se decodea Then devuelve el exp en epoch ms', () => {
    // Arrange
    const exp = nowSec() + 900
    const token = makeJwt({ sub: 'usr_01', exp })

    // Act
    const result = getJwtExpiry(token)

    // Assert
    expect(result).toBe(exp * 1000)
  })

  it('Given un token invalido When se decodea Then devuelve null', () => {
    // Act
    const result = getJwtExpiry('not-a-jwt')

    // Assert
    expect(result).toBe(null)
  })
})

describe('isJwtExpired', () => {
  it('Given un JWT con exp pasado When se evalua Then devuelve true', () => {
    // Arrange
    const token = makeJwt({ sub: 'usr_01', exp: nowSec() - 10 })

    // Act
    const result = isJwtExpired(token)

    // Assert
    expect(result).toBe(true)
  })

  it('Given un JWT con exp futuro When se evalua Then devuelve false', () => {
    // Arrange
    const token = makeJwt({ sub: 'usr_01', exp: nowSec() + 900 })

    // Act
    const result = isJwtExpired(token)

    // Assert
    expect(result).toBe(false)
  })

  it('Given un token invalido When se evalua Then devuelve true (exp null)', () => {
    // Act: cubre la rama `exp === null` -> true dentro de isJwtExpired
    const result = isJwtExpired('not-a-jwt')

    // Assert
    expect(result).toBe(true)
  })
})
