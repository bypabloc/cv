'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { settingsKeys } from '../api/query-keys'
import { settingsClient } from '../api/settings-client'

/**
 * @function useChangeEmailInitiate
 * @description Inicia el cambio de email (users.profile.change-email). En exito
 *   muestra el aviso de "revisa tu correo". NO invalida el perfil todavia (el
 *   email cambia solo al confirmar).
 */
export function useChangeEmailInitiate() {
  return useMutation({
    mutationFn: settingsClient.changeEmail,
    onSuccess: () => {
      toast.success('Te enviamos un correo de confirmacion al nuevo email')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}

/**
 * @function useConfirmEmailChange
 * @description Confirma el cambio de email con el token (users.profile.
 *   confirm-email-change). En exito invalida `settingsKeys.profile()`.
 */
export function useConfirmEmailChange() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: settingsClient.confirmEmailChange,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.profile() })
      toast.success('Email actualizado')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
