'use client'

import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ROUTES } from '@/lib/routes'
import { authClient } from '../api/auth-client'
import { useAuthStore } from '../store/use-auth-store'

/**
 * @function useLoginVerifyTotp
 * @description Paso final del login con MFA TOTP. Setea tokens + user y navega
 *   al app shell. El 400 (codigo invalido) se muestra como toast.
 */
export function useLoginVerifyTotp() {
  const router = useRouter()
  const setTokens = useAuthStore((s) => s.setTokens)

  return useMutation({
    mutationFn: authClient.loginVerifyTotp,
    onSuccess: ({ data }) => {
      setTokens(data.access_token, data.refresh_token, data.user)
      router.replace(ROUTES.admin.root)
      toast.success('Sesion iniciada')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
