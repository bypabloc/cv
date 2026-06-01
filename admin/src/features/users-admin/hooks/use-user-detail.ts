'use client'

import { useQuery } from '@tanstack/react-query'
import { adminKeys } from '../api/query-keys'
import { usersAdminClient } from '../api/users-admin-client'

/**
 * @function useUserDetail
 * @description Detalle de un usuario (admin.get-user). queryKey
 *   `adminKeys.user(userId)`, staleTime 0 (siempre fresh). Solo corre con
 *   `userId` truthy (deep-link `?user=<id>`).
 * @param {string | null} userId - id del usuario o null (drawer cerrado)
 */
export function useUserDetail(userId: string | null) {
  return useQuery({
    queryKey: adminKeys.user(userId ?? ''),
    queryFn: async () => {
      const { data } = await usersAdminClient.getUser({
        user_id: userId as string,
      })
      return data.user
    },
    enabled: Boolean(userId),
    staleTime: 0,
  })
}
