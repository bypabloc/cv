import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useDisableUser } from '@/features/users-admin/hooks/use-disable-user'

/**
 * @module tests/unit/features/users-admin/use-disable-user
 * @description Verifica que disable-user invalida las queries `admin` en exito.
 */

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const invalidateSpy = vi.spyOn(client, 'invalidateQueries')
  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>
  }
  return { Wrapper, invalidateSpy }
}

describe('useDisableUser', () => {
  it('Given un user When disable Then invalida users + user + actions en exito', async () => {
    // Arrange
    const { Wrapper, invalidateSpy } = createWrapper()
    const { result } = renderHook(() => useDisableUser(), { wrapper: Wrapper })

    // Act
    await act(async () => {
      await result.current.mutateAsync({ user_id: 'usr_02' })
    })

    // Assert
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['admin', 'users'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['admin', 'user', 'usr_02'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['admin', 'actions'],
    })
  })
})
