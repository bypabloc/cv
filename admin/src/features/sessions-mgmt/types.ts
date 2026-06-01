import type { AccountSession, AccountStatus } from '@/types/models'

/**
 * @module features/sessions-mgmt/types
 * @description Tipos del dominio de gestion de sesiones de la cuenta auth.
 *   `AccountSession` y `AccountStatus` viven en `@/types/models` (contrato real
 *   del Lambda `users` operation `status`); aqui se re-exportan por comodidad y
 *   se define el payload de revocacion.
 */

export type { AccountSession, AccountStatus }

/** users.status.revoke-session */
export interface RevokeSessionPayload {
  session_id: string
}
