'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ApiError } from '@/lib/api-client'
import { authClient } from '../api/auth-client'
import { authKeys } from '../api/query-keys'

/**
 * @function useDeleteCredential
 * @description Borra un passkey. El 409 (MUST_KEEP_ONE_MFA_METHOD) NO invalida
 *   la query: muestra el error y propaga. En exito invalida `authKeys.webauthn()`.
 */
export function useDeleteCredential() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authClient.webauthnDeleteCredential,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.webauthn() })
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        toast.error('Debes conservar al menos un metodo MFA')
        return
      }
      toast.error(error.message)
    },
  })
}
