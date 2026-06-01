/**
 * @module features/users-admin
 * @description Barrel publico del feature users-admin (gestion de OTROS
 *   usuarios, solo admin). Export explicito (no `export *`) de lo que consume
 *   la page `/users`.
 */

// Componentes
export { AdminActionsLog } from './components/admin-actions-log'
export { StatusBadge } from './components/status-badge'
export { UserActionsMenu } from './components/user-actions-menu'
export { UserDetailDrawer } from './components/user-detail-drawer'
export { UsersTable } from './components/users-table'
// Hooks
export { useAdminActions } from './hooks/use-admin-actions'
export { useDeleteUser } from './hooks/use-delete-user'
export { useDisableUser } from './hooks/use-disable-user'
export { useEnableUser } from './hooks/use-enable-user'
export { useForceLogout } from './hooks/use-force-logout'
export { useUserDetail } from './hooks/use-user-detail'
export { useUsersList } from './hooks/use-users-list'
// Tipos publicos
export type { ListUsersPayload, UserIdPayload } from './types'
