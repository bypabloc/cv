import type { AuthenticationResponseJSON } from '@simplewebauthn/browser'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import { server } from '@tests/mocks/server'
import { HttpResponse, http } from 'msw'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useWebauthnLoginVerify } from '@/features/auth/hooks/use-webauthn-login-verify'
import { useAuthStore } from '@/features/auth/store/use-auth-store'

/**
 * @module tests/unit/features/auth/hooks/use-webauthn-login-verify
 * @description Verifica que un 401 (clone detection) NO setee tokens.
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

const FAKE_RESPONSE = {
  id: 'cred',
  rawId: 'cred',
  response: {},
  type: 'public-key',
  clientExtensionResults: {},
} as unknown as AuthenticationResponseJSON

describe('useWebauthnLoginVerify', () => {
  it('Given 401 clone detection When mutate Then no setea tokens', async () => {
    // Arrange: sin refresh token, skipAuth=true en el client -> el 401 NO
    // dispara el mutex de refresh, propaga como ApiError 401.
    useAuthStore.setState({ refreshToken: null })
    server.use(
      http.post(`${API}/auth`, () =>
        HttpResponse.json(
          {
            error: 'WEBAUTHN_CLONE_DETECTED',
            code: 4010,
            message: 'Clone detectado',
          },
          { status: 401 },
        ),
      ),
    )
    const { result } = renderHook(() => useWebauthnLoginVerify(), { wrapper })

    // Act
    await act(async () => {
      await result.current
        .mutateAsync({ challenge_id: 'chal', response: FAKE_RESPONSE })
        .catch(() => undefined)
    })

    // Assert
    expect(useAuthStore.getState().accessToken).toBe(null)
    expect(useAuthStore.getState().user).toBe(null)
  })
})
