'use client'

import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ROUTES } from '@/lib/routes'
import { authClient } from '../api/auth-client'
import { useAuthStore } from '../store/use-auth-store'

/**
 * @function useSetPassword
 * @description Setea la contrasena en el onboarding (verify.set-password,
 *   temp step>=2). Cierra con AuthResponse: setTokens + redirect.
 */
export function useSetPassword() {
  const router = useRouter()
  const setTokens = useAuthStore((s) => s.setTokens)

  return useMutation({
    mutationFn: authClient.setPassword,
    onSuccess: ({ data }) => {
      setTokens(data.access_token, data.refresh_token, data.user)
      router.replace(ROUTES.admin.root)
      toast.success('Contrasena guardada')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
