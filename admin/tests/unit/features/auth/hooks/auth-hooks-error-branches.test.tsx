import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import { server } from '@tests/mocks/server'
import { HttpResponse, http } from 'msw'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useConsumeRecoveryCode } from '@/features/auth/hooks/use-consume-recovery-code'
import { useDeleteCredential } from '@/features/auth/hooks/use-delete-credential'
import { useDisableMfa } from '@/features/auth/hooks/use-disable-mfa'
import { useLoginVerifyCode } from '@/features/auth/hooks/use-login-verify-code'
import { useLoginVerifyPassword } from '@/features/auth/hooks/use-login-verify-password'
import { useRegisterStart } from '@/features/auth/hooks/use-register-start'
import { useRegisterVerifyCode } from '@/features/auth/hooks/use-register-verify-code'
import { useSetPassword } from '@/features/auth/hooks/use-set-password'
import { useWebauthnLoginVerify } from '@/features/auth/hooks/use-webauthn-login-verify'
import { ApiError } from '@/lib/api-client'

/**
 * @module tests/unit/features/auth/hooks/auth-hooks-error-branches
 * @description Cubre las ramas onError "fallback" (toast.error(error.message))
 *   de los hooks de mutation: un 500 generico NO matchea los status especiales
 *   (409/403/401), forzando el camino del else. Tambien cubre los onSuccess
 *   faltantes (delete-credential invalidate) y el verify-password con MFA.
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

function force500() {
  server.use(
    http.post(`${API}/auth`, () =>
      HttpResponse.json(
        { error: 'SERVER_ERROR', code: 5000, message: 'Boom' },
        { status: 500 },
      ),
    ),
  )
}

describe('useDeleteCredential onSuccess', () => {
  it('Given delete OK When mutate Then resuelve (invalida la query)', async () => {
    // Arrange: el handler default devuelve {credentials: []}
    const { result } = renderHook(() => useDeleteCredential(), { wrapper })

    // Act
    const data = await act(async () =>
      result.current.mutateAsync({ credential_id: 'cred_01' }),
    )

    // Assert
    expect(data.data.credentials).toEqual([])
  })
})

describe('useDeleteCredential onError fallback', () => {
  it('Given un 500 generico When mutate Then propaga ApiError (rama else)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useDeleteCredential(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({ credential_id: 'cred_01' })
        .catch((e: unknown) => e),
    )

    // Assert
    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useDisableMfa onSuccess + onError fallback', () => {
  it('Given disable OK When mutate Then resuelve (invalida la query)', async () => {
    // Arrange: override a 200 para tocar el onSuccess
    server.use(
      http.post(`${API}/auth`, () =>
        HttpResponse.json({
          is_valid: true,
          code: 0,
          data: { methods: [], webauthn_count: 0, total_mfa: 1 },
        }),
      ),
    )
    const { result } = renderHook(() => useDisableMfa(), { wrapper })

    // Act
    const data = await act(async () =>
      result.current.mutateAsync({ kind: 'totp' }),
    )

    // Assert
    expect(data.data.total_mfa).toBe(1)
  })

  it('Given un 500 generico When mutate Then propaga ApiError (rama else)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useDisableMfa(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current.mutateAsync({ kind: 'totp' }).catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useConsumeRecoveryCode onError fallback', () => {
  it('Given un 500 generico When mutate Then propaga ApiError (rama else)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useConsumeRecoveryCode(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({ code: 'ABCDEFGHJ0', temp_token: 'temp' })
        .catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useWebauthnLoginVerify onError fallback', () => {
  it('Given un 500 generico When mutate Then propaga ApiError (rama else)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useWebauthnLoginVerify(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({
          challenge_id: 'chal_02',
          response: {
            id: 'x',
            rawId: 'x',
            type: 'public-key',
            clientExtensionResults: {},
            response: {
              authenticatorData: 'a',
              clientDataJSON: 'c',
              signature: 's',
              userHandle: undefined,
            },
          },
        })
        .catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useRegisterStart onError fallback', () => {
  it('Given un 500 generico (no 409) When mutate Then propaga ApiError', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useRegisterStart(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({
          email: 'new@test.com',
          niche: 'fintech',
          cf_turnstile_response: 'tok',
        })
        .catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useLoginVerifyCode onError', () => {
  it('Given un 500 generico When mutate Then propaga ApiError (toca onError)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useLoginVerifyCode(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({ code: '12345678', temp_token: 'temp' })
        .catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useRegisterVerifyCode onError', () => {
  it('Given un 500 generico When mutate Then propaga ApiError (toca onError)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useRegisterVerifyCode(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({ code: '12345678', temp_token: 'temp' })
        .catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useSetPassword onError', () => {
  it('Given un 500 generico When mutate Then propaga ApiError (toca onError)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useSetPassword(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({ password: 'una-pass-larga-1', temp_token: 'temp' })
        .catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })
})

describe('useLoginVerifyPassword onError + MFA sin callback', () => {
  it('Given un 500 generico When mutate Then propaga ApiError (toca onError)', async () => {
    // Arrange
    force500()
    const { result } = renderHook(() => useLoginVerifyPassword(), { wrapper })

    // Act
    const error = await act(async () =>
      result.current
        .mutateAsync({ temp_token: 'temp', password: 'p' })
        .catch((e: unknown) => e),
    )

    // Assert
    expect((error as ApiError).status).toBe(500)
  })

  it('Given MFA pendiente sin onMfaRequired When mutate Then setea temp y no rompe', async () => {
    // Arrange: respuesta TempTokenResponse sin `methods` (cubre el ?? [])
    server.use(
      http.post(`${API}/auth`, () =>
        HttpResponse.json({
          is_valid: true,
          code: 0,
          data: { temp_token: 'temp-mfa', user_id: 'usr_01', expires_in: 300 },
        }),
      ),
    )
    const { result } = renderHook(() => useLoginVerifyPassword(), { wrapper })

    // Act: sin opts.onMfaRequired -> cubre `opts?.onMfaRequired?.(...)` undefined
    await act(async () => {
      await result.current.mutateAsync({ temp_token: 'temp', password: 'p' })
    })

    // Assert
    expect(result.current.isSuccess).toBe(true)
  })

  it('Given MFA con callback pero sin methods When mutate Then llama con [] (rama ?? derecha)', async () => {
    // Arrange: TempTokenResponse sin `methods` + callback presente
    server.use(
      http.post(`${API}/auth`, () =>
        HttpResponse.json({
          is_valid: true,
          code: 0,
          data: { temp_token: 'temp-mfa', user_id: 'usr_01', expires_in: 300 },
        }),
      ),
    )
    const onMfaRequired = vi.fn()
    const { result } = renderHook(
      () => useLoginVerifyPassword({ onMfaRequired }),
      { wrapper },
    )

    // Act: cubre `data.methods ?? []` (right) + `opts?.onMfaRequired?.()` called
    await act(async () => {
      await result.current.mutateAsync({ temp_token: 'temp', password: 'p' })
    })

    // Assert
    expect(onMfaRequired).toHaveBeenCalledWith([])
  })
})
