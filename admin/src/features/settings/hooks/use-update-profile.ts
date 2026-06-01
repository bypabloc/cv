'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { settingsKeys } from '../api/query-keys'
import { settingsClient } from '../api/settings-client'

/**
 * @function useUpdateProfile
 * @description Actualiza el perfil (users.profile.update). En exito invalida
 *   `settingsKeys.profile()` y muestra un toast.
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: settingsClient.updateProfile,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.profile() })
      toast.success('Perfil actualizado')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
