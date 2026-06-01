import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { useSessionRefresh } from '@/features/auth/hooks/use-session-refresh'
import { useAuthStore } from '@/features/auth/store/use-auth-store'

/**
 * @module tests/unit/features/auth/hooks/use-session-refresh
 * @description Cubre la rama `refreshToken ?? ''` cuando el store no tiene
 *   refresh (envia string vacio). El handler MSW de refresh siempre responde
 *   200, asi que igual setea tokens.
 */

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useSessionRefresh sin refresh en store', () => {
  it('Given refreshToken null When mutate Then usa string vacio (rama ?? "")', async () => {
    // Arrange: store sin refresh (reset por setup) -> refreshToken null
    expect(useAuthStore.getState().refreshToken).toBe(null)
    const { result } = renderHook(() => useSessionRefresh(), { wrapper })

    // Act
    await act(async () => {
      await result.current.mutateAsync()
    })

    // Assert: el MSW responde 200 -> setea el access nuevo
    expect(useAuthStore.getState().accessToken).not.toBe(null)
  })
})
