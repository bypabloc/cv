'use client'

import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ROUTES } from '@/lib/routes'
import type { AuthResponse, TempTokenResponse } from '@/types/api'
import { authClient } from '../api/auth-client'
import { useAuthStore } from '../store/use-auth-store'

type Methods = NonNullable<TempTokenResponse['methods']>

/**
 * @function isAuthResponse
 * @description Discrimina el payload de login.verify-password: AuthResponse
 *   (login directo, sin MFA) vs TempTokenResponse step=2 (con MFA).
 */
function isAuthResponse(
  payload: AuthResponse | TempTokenResponse,
): payload is AuthResponse {
  return 'access_token' in payload
}

/**
 * @function useLoginVerifyPassword
 * @description Dispara login.verify-password. Sin MFA: setTokens + redirect.
 *   Con MFA: guarda el temp step=2 e informa al caller los `methods` via el
 *   callback `onMfaRequired` para que avance al paso TOTP/recovery.
 *
 * @param {object} [opts] - Callbacks de control de flujo
 * @param {(methods: Methods) => void} [opts.onMfaRequired] - MFA pendiente
 */
export function useLoginVerifyPassword(opts?: {
  onMfaRequired?: (methods: Methods) => void
}) {
  const router = useRouter()
  const setTokens = useAuthStore((s) => s.setTokens)
  const setTempToken = useAuthStore((s) => s.setTempToken)

  return useMutation({
    mutationFn: authClient.loginVerifyPassword,
    onSuccess: ({ data }) => {
      if (isAuthResponse(data)) {
        setTokens(data.access_token, data.refresh_token, data.user)
        router.replace(ROUTES.admin.root)
        toast.success('Sesion iniciada')
        return
      }
      setTempToken(data.temp_token)
      opts?.onMfaRequired?.(data.methods ?? [])
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
