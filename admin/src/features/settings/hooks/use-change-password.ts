'use client'

import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ApiError } from '@/lib/api-client'
import { settingsClient } from '../api/settings-client'

/**
 * @function useChangePassword
 * @description Cambia la contrasena del usuario autenticado contra la action
 *   REAL `users.profile.change-password` (validada con el access JWT). En
 *   exito muestra el toast 'Contrasena actualizada' (la sesion sigue viva
 *   porque el backend preserva la sesion actual). Un 401 INVALID_PASSWORD
 *   (code 4005) se muestra como toast inline y NO rompe la app.
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: settingsClient.changePassword,
    onSuccess: () => {
      toast.success('Contrasena actualizada')
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 401) {
        toast.error('La contrasena actual es incorrecta')
        return
      }
      toast.error(error.message)
    },
  })
}
