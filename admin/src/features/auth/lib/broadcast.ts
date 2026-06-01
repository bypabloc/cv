/**
 * @module broadcast
 * @description Helpers de BroadcastChannel para sync multi-tab de auth.
 *   Guard SSR/build: `typeof BroadcastChannel === 'undefined'`.
 */

export const AUTH_CHANNEL = 'portfolio_auth'

export interface AuthBroadcastMessage {
  type: 'LOGOUT' | 'TOKEN_REFRESH'
  token?: string
}

/**
 * @function broadcastAuth
 * @description Emite un mensaje a las demas tabs (LOGOUT / TOKEN_REFRESH).
 * @param {AuthBroadcastMessage} message - Mensaje a emitir
 */
export function broadcastAuth(message: AuthBroadcastMessage): void {
  if (typeof BroadcastChannel === 'undefined') return
  const channel = new BroadcastChannel(AUTH_CHANNEL)
  channel.postMessage(message)
  channel.close()
}
