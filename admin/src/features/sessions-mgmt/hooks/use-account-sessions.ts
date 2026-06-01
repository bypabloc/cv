'use client'

import { useQuery } from '@tanstack/react-query'
import { sessionsKeys } from '../api/query-keys'
import { sessionsMgmtClient } from '../api/sessions-mgmt-client'

/**
 * @function useAccountSessions
 * @description Sesiones activas de la cuenta (users.status.list-sessions).
 *   queryKey `sessionsKeys.sessions()`, staleTime 30s. Devuelve el array
 *   `AccountSession[]` desempaquetado.
 */
export function useAccountSessions() {
  return useQuery({
    queryKey: sessionsKeys.sessions(),
    queryFn: async () => {
      const { data } = await sessionsMgmtClient.listSessions()
      return data.sessions
    },
    staleTime: 30_000,
  })
}
