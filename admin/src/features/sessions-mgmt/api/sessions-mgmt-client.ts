import { apiFetch } from '@/lib/api-client'
import type { Envelope, SessionsResponse, StatusResponse } from '@/types/api'
import type { RevokeSessionPayload } from '../types'

/**
 * @module features/sessions-mgmt/api/sessions-mgmt-client
 * @description Cliente tipado del Lambda `users` (operation `status`) para la
 *   gestion de las sesiones de MI cuenta auth. Cada action hace `POST /users`
 *   con body JSON `{operation: 'status', action, data}` y respuesta envuelta
 *   en `{is_valid, code, data}`. El access JWT lo agrega el api-client (Bearer).
 *
 * NO confundir con la feature `sessions` de metricas (tracking de visitantes):
 * esta feature opera sobre las sesiones del usuario autenticado.
 */
export const sessionsMgmtClient = {
  /** status.get: estado de la cuenta + current_session_id. */
  getStatus: () =>
    apiFetch<Envelope<StatusResponse>>('/users', {
      method: 'POST',
      body: { operation: 'status', action: 'get', data: {} },
    }),

  /** status.list-sessions: sesiones activas de la cuenta. */
  listSessions: () =>
    apiFetch<Envelope<SessionsResponse>>('/users', {
      method: 'POST',
      body: { operation: 'status', action: 'list-sessions', data: {} },
    }),

  /**
   * status.revoke-session: revoca una sesion por id. 400
   * CANNOT_REVOKE_CURRENT_SESSION si se intenta revocar la sesion actual
   * (usar logout en su lugar). En exito invalida la lista de sesiones.
   */
  revokeSession: (data: RevokeSessionPayload) =>
    apiFetch<Envelope<{ ok: true }>>('/users', {
      method: 'POST',
      body: { operation: 'status', action: 'revoke-session', data },
    }),
}
