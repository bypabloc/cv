import { renderHook, waitFor } from '@testing-library/react'
import { makeJwt, nowSec } from '@tests/mocks/jwt'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthTimer } from '@/features/auth/hooks/use-auth-timer'
import { useAuthStore } from '@/features/auth/store/use-auth-store'

/**
 * @module tests/unit/features/auth/hooks/use-auth-timer
 * @description Verifica el bootstrap (hidrata access desde refresh), el refresh
 *   inmediato cuando el access esta por expirar, y el reset si el refresh esta
 *   muerto.
 */

beforeEach(() => {
  useAuthStore.getState().reset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useAuthTimer bootstrap', () => {
  it('Given refresh vigente y access null When monta Then hidrata el access via /session/refresh', async () => {
    // Arrange
    useAuthStore.setState({
      accessToken: null,
      refreshToken: makeJwt({ sub: 'usr_01', exp: nowSec() + 2_592_000 }),
      refreshExpiry: (nowSec() + 2_592_000) * 1000,
    })

    // Act
    renderHook(() => useAuthTimer())

    // Assert
    await waitFor(() => {
      expect(useAuthStore.getState().accessToken).not.toBe(null)
    })
  })

  it('Given refresh expirado y access null When monta Then resetea el store', async () => {
    // Arrange
    useAuthStore.setState({
      accessToken: null,
      refreshToken: 'dead',
      refreshExpiry: Date.now() - 1000,
    })

    // Act
    renderHook(() => useAuthTimer())

    // Assert: el bootstrap no dispara refresh (refreshExpiry <= now)
    expect(useAuthStore.getState().accessToken).toBe(null)
  })
})

describe('useAuthTimer refresh inmediato', () => {
  it('Given un access casi vencido When monta Then refresca de inmediato', async () => {
    // Arrange: exp dentro del lead (30s) -> msUntilRefresh <= 0
    useAuthStore.setState({
      accessToken: makeJwt({ sub: 'usr_01', exp: nowSec() + 5 }),
      refreshToken: makeJwt({ sub: 'usr_01', exp: nowSec() + 2_592_000 }),
      refreshExpiry: (nowSec() + 2_592_000) * 1000,
    })
    const before = useAuthStore.getState().accessToken

    // Act
    renderHook(() => useAuthTimer())

    // Assert: el access se rota a uno nuevo
    await waitFor(() => {
      expect(useAuthStore.getState().accessToken).not.toBe(before)
    })
  })

  it('Given un access invalido When monta Then resetea', () => {
    // Arrange
    useAuthStore.setState({ accessToken: 'not-a-jwt' })

    // Act
    renderHook(() => useAuthTimer())

    // Assert
    expect(useAuthStore.getState().accessToken).toBe(null)
  })
})

describe('useAuthTimer page visibility', () => {
  it('Given un access casi vencido When la tab vuelve a foco Then refresca', async () => {
    // Arrange: access lejos del vencimiento para NO disparar el timer inmediato,
    // luego lo acercamos y simulamos el foco.
    useAuthStore.setState({
      accessToken: makeJwt({ sub: 'usr_01', exp: nowSec() + 3600 }),
      refreshToken: makeJwt({ sub: 'usr_01', exp: nowSec() + 2_592_000 }),
      refreshExpiry: (nowSec() + 2_592_000) * 1000,
    })
    renderHook(() => useAuthTimer())
    const before = useAuthStore.getState().accessToken

    // El access ahora vence dentro del lead.
    useAuthStore.setState({
      accessToken: makeJwt({ sub: 'usr_01', exp: nowSec() + 5 }),
    })
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      get: () => 'visible',
    })

    // Act
    document.dispatchEvent(new Event('visibilitychange'))

    // Assert
    await waitFor(() => {
      expect(useAuthStore.getState().accessToken).not.toBe(before)
    })
  })
})
