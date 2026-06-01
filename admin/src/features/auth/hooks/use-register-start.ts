'use client'

import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ApiError } from '@/lib/api-client'
import { ROUTES } from '@/lib/routes'
import { authClient } from '../api/auth-client'
import { useAuthStore } from '../store/use-auth-store'

/**
 * @function useRegisterStart
 * @description Dispara register.start: guarda el temp_token y navega a
 *   `/verify?flow=register`. Mapea el 409 (email ya registrado) a un toast.
 */
export function useRegisterStart() {
  const router = useRouter()
  const setTempToken = useAuthStore((s) => s.setTempToken)

  return useMutation({
    mutationFn: authClient.registerStart,
    onSuccess: ({ data }) => {
      setTempToken(data.temp_token)
      router.push(`${ROUTES.auth.verify}?flow=register`)
      toast.success('Te enviamos un email con un magic-link y un codigo')
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        toast.error('Email ya registrado', {
          description: 'Inicia sesion en su lugar.',
        })
        return
      }
      toast.error(error.message)
    },
  })
}
