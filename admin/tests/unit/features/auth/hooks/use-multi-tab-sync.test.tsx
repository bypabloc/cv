import { renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useMultiTabSync } from '@/features/auth/hooks/use-multi-tab-sync'
import { useAuthStore } from '@/features/auth/store/use-auth-store'

/**
 * @module tests/unit/features/auth/hooks/use-multi-tab-sync
 * @description Verifica que el listener BroadcastChannel resetee el store al
 *   recibir LOGOUT y actualice el access al recibir TOKEN_REFRESH.
 */

type Listener = (event: MessageEvent) => void

afterEach(() => {
  vi.unstubAllGlobals()
})

function stubChannel(): { emit: (data: unknown) => void } {
  let handler: Listener | null = null
  class FakeChannel {
    set onmessage(fn: Listener) {
      handler = fn
    }
    close = vi.fn()
  }
  vi.stubGlobal('BroadcastChannel', FakeChannel)
  return {
    emit: (data: unknown) => handler?.({ data } as MessageEvent),
  }
}

describe('useMultiTabSync', () => {
  it('Given un mensaje LOGOUT When llega Then resetea el store', () => {
    // Arrange
    const channel = stubChannel()
    useAuthStore.setState({ accessToken: 'tok' })
    renderHook(() => useMultiTabSync())

    // Act
    channel.emit({ type: 'LOGOUT' })

    // Assert
    expect(useAuthStore.getState().accessToken).toBe(null)
  })

  it('Given un mensaje TOKEN_REFRESH When llega Then setea el nuevo access', () => {
    // Arrange
    const channel = stubChannel()
    renderHook(() => useMultiTabSync())

    // Act
    channel.emit({ type: 'TOKEN_REFRESH', token: 'nuevo' })

    // Assert
    expect(useAuthStore.getState().accessToken).toBe('nuevo')
  })
})
