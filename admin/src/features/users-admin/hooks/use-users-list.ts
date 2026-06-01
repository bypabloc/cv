'use client'

import { useQuery } from '@tanstack/react-query'
import { adminKeys } from '../api/query-keys'
import { usersAdminClient } from '../api/users-admin-client'
import type { ListUsersPayload } from '../types'

/**
 * @function useUsersList
 * @description Lista los usuarios (admin.list-users) con paginacion.
 *   queryKey `adminKeys.users({page, page_size})`, staleTime 30s. Si el caller
 *   no es admin el backend responde 404; el error se propaga (la page lo maneja
 *   con un estado de acceso denegado, anti-enumeration).
 * @param {ListUsersPayload} [params] - paginacion opcional
 */
export function useUsersList(params: ListUsersPayload = {}) {
  return useQuery({
    queryKey: adminKeys.users(params),
    queryFn: async () => {
      const { data } = await usersAdminClient.listUsers(params)
      return data
    },
    staleTime: 30_000,
  })
}
