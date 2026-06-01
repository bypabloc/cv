import type { AuthenticationResponseJSON } from '@simplewebauthn/browser'
import { act, renderHook } from '@testing-library/react'
import { server } from '@tests/mocks/server'
import { makeHookWrapper } from '@tests/utils/hook-wrapper'
import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { useConsumeRecoveryCode } from '@/features/auth/hooks/use-consume-recovery-code'
import { useDeleteCredential } from '@/features/auth/hooks/use-delete-credential'
import { useDisableMfa } from '@/features/auth/hooks/use-disable-mfa'
import { useWebauthnLoginVerify } from '@/features/auth/hooks/use-webauthn-login-verify'
import { useAuthStore } from '@/features/auth/store/use-auth-store'
import { ApiError } from '@/lib/api-client'

/**
 * @module tests/unit/features/auth/hooks/login-mfa-success
 * @description Happy paths de consume-recovery, webauthn-login-verify y
 *   ramas de exito/409 de los hooks de gestion.
 */

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

const API = 'https://api.test.the-full-stack.com'

const FAKE_AUTH = {
  id: 'cred',
  rawId: 'cred',
  response: {},
  type: 'public-key',
  clientExtensionResults: {},
} as unknown as AuthenticationResponseJSON

describe('useConsumeRecoveryCode (exito)', () => {
  it('Given recovery valido When mutate Then setTokens', async () => {
    const { wrapper } = makeHookWrapper()
    const { result } = renderHook(() => useConsumeRecoveryCode(), { wrapper })

    await act(async () => {
      await result.current.mutateAsync({ code: 'ABCDEFGHJ0', temp_token: 't' })
    })

    expect(useAuthStore.getState().accessToken).not.toBe(null)
  })
})

describe('useWebauthnLoginVerify (exito)', () => {
  it('Given verify OK When mutate Then setTokens', async () => {
    const { wrapper } = makeHookWrapper()
    const { result } = renderHook(() => useWebauthnLoginVerify(), { wrapper })

    await act(async () => {
      await result.current.mutateAsync({
        challenge_id: 'chal_02',
        response: FAKE_AUTH,
      })
    })

    expect(useAuthStore.getState().accessToken).not.toBe(null)
  })
})

describe('useDisableMfa (exito)', () => {
  it('Given disable que conserva un metodo When mutate Then resuelve sin error', async () => {
    server.use(
      http.post(`${API}/auth`, () =>
        HttpResponse.json({
          is_valid: true,
          code: 0,
          data: { methods: [], webauthn_count: 1, total_mfa: 1 },
        }),
      ),
    )
    const { wrapper } = makeHookWrapper()
    const { result } = renderHook(() => useDisableMfa(), { wrapper })

    const res = await act(async () =>
      result.current.mutateAsync({ kind: 'totp' }),
    )

    expect(res.data.total_mfa).toBe(1)
  })
})

describe('useDeleteCredential (409)', () => {
  it('Given delete que deja total_mfa 0 When mutate Then propaga ApiError 409', async () => {
    server.use(
      http.post(`${API}/auth`, () =>
        HttpResponse.json(
          { error: 'MUST_KEEP_ONE_MFA_METHOD', code: 4093, message: 'x' },
          { status: 409 },
        ),
      ),
    )
    const { wrapper } = makeHookWrapper()
    const { result } = renderHook(() => useDeleteCredential(), { wrapper })

    const error = await act(async () =>
      result.current
        .mutateAsync({ credential_id: 'cred_01' })
        .catch((e: unknown) => e),
    )

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(409)
  })
})
