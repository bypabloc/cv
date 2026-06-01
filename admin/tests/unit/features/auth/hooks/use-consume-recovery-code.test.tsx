import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import { server } from '@tests/mocks/server'
import { HttpResponse, http } from 'msw'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useConsumeRecoveryCode } from '@/features/auth/hooks/use-consume-recovery-code'
import { useAuthStore } from '@/features/auth/store/use-auth-store'

/**
 * @module tests/unit/features/auth/hooks/use-consume-recovery-code
 * @description Verifica que un 403 RECOVERY_REQUIRES_STRONG_FACTOR NO setee
 *   tokens (el store queda sin cambios).
 */

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

const API = 'https://api.test.the-full-stack.com'

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useConsumeRecoveryCode', () => {
  it('Given 403 RECOVERY_REQUIRES_STRONG_FACTOR When mutate Then no setea tokens', async () => {
    // Arrange
    server.use(
      http.post(`${API}/auth`, () =>
        HttpResponse.json(
          {
            error: 'RECOVERY_REQUIRES_STRONG_FACTOR',
            code: 4030,
            message: 'Factor fuerte requerido',
          },
          { status: 403 },
        ),
      ),
    )
    const { result } = renderHook(() => useConsumeRecoveryCode(), { wrapper })

    // Act
    await act(async () => {
      await result.current
        .mutateAsync({ code: 'ABCDEFGHJ0', temp_token: 'temp' })
        .catch(() => undefined)
    })

    // Assert
    expect(useAuthStore.getState().accessToken).toBe(null)
    expect(useAuthStore.getState().user).toBe(null)
  })
})
