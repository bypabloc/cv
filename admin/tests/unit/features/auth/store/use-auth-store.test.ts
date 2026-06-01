import { makeJwt, nowSec } from '@tests/mocks/jwt'
import { beforeEach, describe, expect, it } from 'vitest'
import { useAuthStore } from '@/features/auth/store/use-auth-store'
import type { User } from '@/types/models'

/**
 * @module tests/unit/features/auth/store/use-auth-store
 * @description Verifica el contrato del store de auth: setTokens, derived,
 *   reset/clearTokens y la persistencia parcial (partialize).
 */

const USER: User = {
  id: 'usr_01',
  email: 'user@test.com',
  status: 'active',
  has_password: true,
  mfa_methods: [],
}

const STORAGE_KEY = 'portfolio-admin-auth'

beforeEach(() => {
  useAuthStore.getState().reset()
  localStorage.clear()
})

describe('useAuthStore', () => {
  it('Given setTokens When se llama Then setea access (memoria) + refresh + refreshExpiry + user', () => {
    // Arrange
    const access = makeJwt({ sub: 'usr_01', exp: nowSec() + 900 })
    const refreshExp = nowSec() + 2_592_000
    const refresh = makeJwt({ sub: 'usr_01', exp: refreshExp })

    // Act
    useAuthStore.getState().setTokens(access, refresh, USER)

    // Assert
    const state = useAuthStore.getState()
    expect(state.accessToken).toBe(access)
    expect(state.refreshToken).toBe(refresh)
    expect(state.refreshExpiry).toBe(refreshExp * 1000)
    expect(state.user).toEqual(USER)
  })

  it('Given sin token When isAuthenticated Then retorna false', () => {
    // Act
    const result = useAuthStore.getState().isAuthenticated()

    // Assert
    expect(result).toBe(false)
  })

  it('Given un access expirado When isAccessExpired Then retorna true', () => {
    // Arrange
    useAuthStore
      .getState()
      .setAccessToken(makeJwt({ sub: 'usr_01', exp: nowSec() - 10 }))

    // Act
    const result = useAuthStore.getState().isAccessExpired()

    // Assert
    expect(result).toBe(true)
  })

  it('Given un access vigente + user When isAuthenticated Then retorna true', () => {
    // Arrange
    useAuthStore
      .getState()
      .setTokens(
        makeJwt({ sub: 'usr_01', exp: nowSec() + 900 }),
        makeJwt({ sub: 'usr_01', exp: nowSec() + 2_592_000 }),
        USER,
      )

    // Act
    const result = useAuthStore.getState().isAuthenticated()

    // Assert
    expect(result).toBe(true)
  })

  it('Given estado seteado When clearTokens Then limpia todo', () => {
    // Arrange
    useAuthStore.getState().setTokens('a', 'r', USER, nowSec() * 1000 + 1000)
    useAuthStore.getState().setTempToken('temp')

    // Act
    useAuthStore.getState().clearTokens()

    // Assert
    const state = useAuthStore.getState()
    expect(state.accessToken).toBe(null)
    expect(state.refreshToken).toBe(null)
    expect(state.refreshExpiry).toBe(null)
    expect(state.tempToken).toBe(null)
    expect(state.user).toBe(null)
  })

  it('Given estado seteado When reset Then limpia todo', () => {
    // Arrange
    useAuthStore.getState().setTokens('a', 'r', USER, 123)

    // Act
    useAuthStore.getState().reset()

    // Assert
    expect(useAuthStore.getState().accessToken).toBe(null)
    expect(useAuthStore.getState().user).toBe(null)
  })

  it('Given setRefreshToken con null When se llama Then refreshExpiry queda null', () => {
    // Arrange: primero un refresh valido para que refreshExpiry no sea null
    useAuthStore
      .getState()
      .setRefreshToken(makeJwt({ sub: 'usr_01', exp: nowSec() + 900 }))

    // Act: la rama false del ternario `token ? decodeExp(token) : null`
    useAuthStore.getState().setRefreshToken(null)

    // Assert
    const state = useAuthStore.getState()
    expect(state.refreshToken).toBe(null)
    expect(state.refreshExpiry).toBe(null)
  })

  it('Given setRefreshToken con un JWT When se llama Then deriva el refreshExpiry', () => {
    // Arrange
    const exp = nowSec() + 1800
    const refresh = makeJwt({ sub: 'usr_01', exp })

    // Act: la rama true del ternario
    useAuthStore.getState().setRefreshToken(refresh)

    // Assert
    expect(useAuthStore.getState().refreshExpiry).toBe(exp * 1000)
  })

  it('Given sin access When isAccessExpired Then retorna true (rama !accessToken)', () => {
    // Act
    const result = useAuthStore.getState().isAccessExpired()

    // Assert
    expect(result).toBe(true)
  })

  it('Given un access invalido When isAccessExpired Then retorna true (exp null)', () => {
    // Arrange
    useAuthStore.getState().setAccessToken('not-a-jwt')

    // Act
    const result = useAuthStore.getState().isAccessExpired()

    // Assert
    expect(result).toBe(true)
  })

  it('Given setTokens sin refreshExpiry explicito When se llama Then lo deriva del refresh', () => {
    // Arrange: la rama `refreshExpiry ?? decodeExp(refresh)` cae a decodeExp
    const exp = nowSec() + 2_592_000
    const refresh = makeJwt({ sub: 'usr_01', exp })

    // Act
    useAuthStore.getState().setTokens('access', refresh, USER)

    // Assert
    expect(useAuthStore.getState().refreshExpiry).toBe(exp * 1000)
  })

  it('Given setTokens + setTempToken When se persiste Then localStorage solo guarda refreshToken, refreshExpiry y user', () => {
    // Arrange
    const refresh = makeJwt({ sub: 'usr_01', exp: nowSec() + 2_592_000 })

    // Act
    useAuthStore.getState().setTokens('access-jwt', refresh, USER, 999)
    useAuthStore.getState().setTempToken('temp-jwt')

    // Assert
    const raw = localStorage.getItem(STORAGE_KEY)
    expect(raw).not.toBe(null)
    const persisted = JSON.parse(raw as string).state
    expect(persisted).toEqual({
      refreshToken: refresh,
      refreshExpiry: 999,
      user: USER,
    })
    expect('accessToken' in persisted).toBe(false)
    expect('tempToken' in persisted).toBe(false)
  })
})
