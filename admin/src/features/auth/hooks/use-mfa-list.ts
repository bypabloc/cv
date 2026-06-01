'use client'

import { useQuery } from '@tanstack/react-query'
import { authClient } from '../api/auth-client'
import { authKeys } from '../api/query-keys'

/**
 * @function useMfaList
 * @description Lista los metodos MFA del usuario (mfa.list). queryKey
 *   `authKeys.mfa()`. Devuelve el `MfaListResponse` desempaquetado.
 */
export function useMfaList() {
  return useQuery({
    queryKey: authKeys.mfa(),
    queryFn: async () => {
      const { data } = await authClient.mfaList()
      return data
    },
  })
}
