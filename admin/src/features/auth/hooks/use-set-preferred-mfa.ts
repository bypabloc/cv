'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { authClient } from '../api/auth-client'
import { authKeys } from '../api/query-keys'

/**
 * @function useSetPreferredMfa
 * @description Marca el metodo MFA preferido. En exito invalida `authKeys.mfa()`.
 */
export function useSetPreferredMfa() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authClient.mfaSetPreferred,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.mfa() })
    },
  })
}
