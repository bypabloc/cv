'use client'

import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ApiError } from '@/lib/api-client'
import { ROUTES } from '@/lib/routes'
import { authClient } from '../api/auth-client'
import { useAuthStore } from '../store/use-auth-store'

/**
 * @function useWebauthnLoginVerify
 * @description Cierra el login passwordless con passkey. En exito setTokens +
 *   redirect. El 401 (clone detection: sign_count regresivo) NO setea tokens:
 *   muestra el error.
 */
export function useWebauthnLoginVerify() {
  const router = useRouter()
  const setTokens = useAuthStore((s) => s.setTokens)

  return useMutation({
    mutationFn: authClient.webauthnLoginVerify,
    onSuccess: ({ data }) => {
      setTokens(data.access_token, data.refresh_token, data.user)
      router.replace(ROUTES.admin.root)
      toast.success('Sesion iniciada')
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 401) {
        toast.error('No pudimos validar el passkey')
        return
      }
      toast.error(error.message)
    },
  })
}
