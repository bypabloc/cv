/**
 * @module features/users-admin/types
 * @description Payloads del Lambda `users` (operation `admin`). Los tipos de
 *   las RESPUESTAS (AdminUser, AdminAction, ListUsersResponse,
 *   AdminActionsResponse) viven en @/types (contrato compartido); aqui solo los
 *   payloads de entrada propios de esta feature.
 */

/** users.admin.list-users — paginacion opcional. */
export interface ListUsersPayload {
  page?: number
  page_size?: number
}

/** Payload comun de get-user / disable / enable / delete / force-logout. */
export interface UserIdPayload {
  user_id: string
}
