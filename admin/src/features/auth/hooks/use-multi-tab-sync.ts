'use client'

import { useEffect } from 'react'
import { AUTH_CHANNEL, type AuthBroadcastMessage } from '../lib/broadcast'
import { useAuthStore } from '../store/use-auth-store'

/**
 * @function useMultiTabSync
 * @description Escucha el canal `portfolio_auth`: LOGOUT resetea el store en
 *   esta tab; TOKEN_REFRESH actualiza el access. Guard SSR/build:
 *   `typeof BroadcastChannel === 'undefined'`.
 */
export function useMultiTabSync(): void {
  useEffect(() => {
    if (typeof BroadcastChannel === 'undefined') return
    const channel = new BroadcastChannel(AUTH_CHANNEL)

    channel.onmessage = (event: MessageEvent<AuthBroadcastMessage>) => {
      if (event.data.type === 'LOGOUT') {
        useAuthStore.getState().reset()
      } else if (event.data.type === 'TOKEN_REFRESH' && event.data.token) {
        useAuthStore.getState().setAccessToken(event.data.token)
      }
    }

    return () => channel.close()
  }, [])
}
