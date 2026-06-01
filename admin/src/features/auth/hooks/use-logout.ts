'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ROUTES } from '@/lib/routes'
import { authClient } from '../api/auth-client'
import { broadcastAuth } from '../lib/broadcast'
import { useAuthStore } from '../store/use-auth-store'

/**
 * @function useLogout
 * @description Cierra la sesion: llama session.logout (best-effort), y en
 *   `onSettled` SIEMPRE limpia el estado local (reset store + queryClient.clear),
 *   notifica las demas tabs (LOGOUT) y redirige a /login.
 */
export function useLogout() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const reset = useAuthStore((s) => s.reset)

  return useMutation({
    mutationFn: async () => {
      await authClient.sessionLogout().catch(() => {
        // El backend pudo fallar: igual cerramos local en onSettled.
      })
    },
    onSettled: () => {
      reset()
      queryClient.clear()
      broadcastAuth({ type: 'LOGOUT' })
      router.replace(ROUTES.auth.login)
      toast.info('Sesion cerrada')
    },
  })
}
