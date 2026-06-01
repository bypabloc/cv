/**
 * @module features/sessions-mgmt
 * @description Barrel publico de la feature de gestion de sesiones de la cuenta
 *   auth (logins activos en otros dispositivos). Consume el Lambda `users`
 *   operation `status`. Autonoma: solo depende de @/components/ui, @/lib y
 *   @/types.
 */

export { sessionsKeys } from './api/query-keys'
export { sessionsMgmtClient } from './api/sessions-mgmt-client'
export { AccountSessionsTable } from './components/account-sessions-table'
export { RevokeSessionButton } from './components/revoke-session-button'
export { useAccountSessions } from './hooks/use-account-sessions'
export { useAccountStatus } from './hooks/use-account-status'
export { useRevokeSession } from './hooks/use-revoke-session'
export type {
  AccountSession,
  AccountStatus,
  RevokeSessionPayload,
} from './types'
