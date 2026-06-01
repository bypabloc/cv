'use client'

import { useQuery } from '@tanstack/react-query'
import { settingsKeys } from '../api/query-keys'
import { settingsClient } from '../api/settings-client'

/**
 * @function useProfile
 * @description Lee el perfil del usuario (users.profile.get). queryKey
 *   `settingsKeys.profile()`. Devuelve el `UserProfile` desempaquetado.
 */
export function useProfile() {
  return useQuery({
    queryKey: settingsKeys.profile(),
    queryFn: async () => {
      const { data } = await settingsClient.getProfile()
      return data.profile
    },
  })
}
