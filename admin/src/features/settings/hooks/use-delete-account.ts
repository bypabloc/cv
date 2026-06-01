'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { useAuthStore } from '@/features/auth'
import { ApiError } from '@/lib/api-client'
import { ROUTES } from '@/lib/routes'
import { settingsClient } from '../api/settings-client'

/**
 * @function useDeleteAccount
 * @description Elimina la cuenta (users.profile.delete-account) con el sentinel
 *   exacto 'DELETE-MY-ACCOUNT'. En exito resetea el store, limpia el
 *   queryClient y redirige a /login. Un 409 CANNOT_DELETE_ADMIN_ACCOUNT NO
 *   redirige: se muestra como toast y la UI lo refleja inline.
 */
export function useDeleteAccount() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const reset = useAuthStore((s) => s.reset)

  return useMutation({
    mutationFn: () =>
      settingsClient.deleteAccount({ confirm: 'DELETE-MY-ACCOUNT' }),
    onSuccess: () => {
      reset()
      queryClient.clear()
      router.replace(ROUTES.auth.login)
      toast.success('Cuenta eliminada')
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        toast.error('No puedes eliminar una cuenta de administrador')
        return
      }
      toast.error(error.message)
    },
  })
}
