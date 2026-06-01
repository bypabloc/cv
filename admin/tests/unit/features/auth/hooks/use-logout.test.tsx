import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useLogout } from '@/features/auth/hooks/use-logout'
import { useAuthStore } from '@/features/auth/store/use-auth-store'
import type { User } from '@/types/models'

/**
 * @module tests/unit/features/auth/hooks/use-logout
 * @description Verifica que logout resetee el store, limpie la query cache,
 *   emita LOGOUT y redirija a /login.
 */

const { replaceMock, broadcastMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  broadcastMock: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
}))

vi.mock('@/features/auth/lib/broadcast', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/features/auth/lib/broadcast')>()
  return { ...actual, broadcastAuth: broadcastMock }
})

const USER: User = {
  id: 'usr_01',
  email: 'u@t.com',
  status: 'active',
  has_password: false,
  mfa_methods: [],
}

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('useLogout', () => {
  it('Given user autenticado When logout Then resetea store + broadcast LOGOUT + redirect /login', async () => {
    // Arrange
    useAuthStore.setState({ accessToken: 'fake-access', user: USER })
    const { result } = renderHook(() => useLogout(), { wrapper })

    // Act
    await act(async () => {
      await result.current.mutateAsync()
    })

    // Assert
    await waitFor(() => {
      expect(useAuthStore.getState().accessToken).toBe(null)
    })
    expect(useAuthStore.getState().user).toBe(null)
    expect(broadcastMock).toHaveBeenCalledWith({ type: 'LOGOUT' })
    expect(replaceMock).toHaveBeenCalledWith('/login')
  })
})
