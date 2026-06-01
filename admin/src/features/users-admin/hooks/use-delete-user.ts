'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { adminKeys } from '../api/query-keys'
import { usersAdminClient } from '../api/users-admin-client'

/**
 * @function useDeleteUser
 * @description Elimina (soft-delete) un usuario (admin.delete-user). En exito
 *   invalida `adminKeys.users` + `adminKeys.user(user_id)` +
 *   `adminKeys.actions` y muestra un toast; en error muestra el mensaje.
 */
export function useDeleteUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: usersAdminClient.deleteUser,
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: adminKeys.usersAll() })
      void queryClient.invalidateQueries({
        queryKey: adminKeys.user(variables.user_id),
      })
      void queryClient.invalidateQueries({ queryKey: adminKeys.actions() })
      toast.success('Usuario eliminado')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
