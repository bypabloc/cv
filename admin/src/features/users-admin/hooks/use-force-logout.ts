'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { adminKeys } from '../api/query-keys'
import { usersAdminClient } from '../api/users-admin-client'

/**
 * @function useForceLogout
 * @description Fuerza el logout de un usuario (admin.force-logout): blacklistea
 *   sus familias de refresh. En exito invalida `adminKeys.users` +
 *   `adminKeys.user(user_id)` + `adminKeys.actions` y muestra un toast; en
 *   error muestra el mensaje.
 */
export function useForceLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: usersAdminClient.forceLogout,
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: adminKeys.usersAll() })
      void queryClient.invalidateQueries({
        queryKey: adminKeys.user(variables.user_id),
      })
      void queryClient.invalidateQueries({ queryKey: adminKeys.actions() })
      toast.success('Sesiones del usuario cerradas')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
