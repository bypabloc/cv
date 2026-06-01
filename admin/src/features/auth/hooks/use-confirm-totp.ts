'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { authClient } from '../api/auth-client'
import { authKeys } from '../api/query-keys'

/**
 * @function useConfirmTotp
 * @description Confirma el TOTP recien seteado. El PRIMER metodo MFA revoca la
 *   familia de refresh (AC-27). En exito invalida `authKeys.mfa()`.
 */
export function useConfirmTotp() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authClient.mfaConfirmTotp,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.mfa() })
    },
  })
}
