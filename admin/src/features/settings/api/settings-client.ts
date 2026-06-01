import { apiFetch } from '@/lib/api-client'
import type { Envelope, ProfileResponse } from '@/types/api'
import type {
  ChangeEmailPayload,
  ChangePasswordPayload,
  ConfirmEmailChangePayload,
  DeleteAccountPayload,
  UpdateProfilePayload,
} from '../types'

/**
 * @module features/settings/api/settings-client
 * @description Cliente tipado del Lambda `users` (operation `profile`). Todas
 *   las actions hacen `POST /users` con body JSON `{operation:'profile',
 *   action, data}` y respuesta envuelta en `{is_valid, code, data}`. Las
 *   actions mfa/webauthn las aporta el feature `auth` (NO se duplican aqui).
 */
export const settingsClient = {
  /** profile.get: perfil completo del usuario autenticado. */
  getProfile: () =>
    apiFetch<Envelope<ProfileResponse>>('/users', {
      method: 'POST',
      body: { operation: 'profile', action: 'get', data: {} },
    }),

  /** profile.update: actualiza el display_name (u otros campos de perfil). */
  updateProfile: (data: UpdateProfilePayload) =>
    apiFetch<Envelope<ProfileResponse>>('/users', {
      method: 'POST',
      body: { operation: 'profile', action: 'update', data },
    }),

  /** profile.change-email: inicia el cambio (envia confirmacion al nuevo). */
  changeEmail: (data: ChangeEmailPayload) =>
    apiFetch<Envelope<{ request_id: string; expires_in: number }>>('/users', {
      method: 'POST',
      body: { operation: 'profile', action: 'change-email', data },
    }),

  /** profile.confirm-email-change: cierra el cambio con el token recibido. */
  confirmEmailChange: (data: ConfirmEmailChangePayload) =>
    apiFetch<Envelope<{ ok: boolean }>>('/users', {
      method: 'POST',
      body: { operation: 'profile', action: 'confirm-email-change', data },
    }),

  /** profile.change-password: cambia la contrasena (access JWT). 401 si la
   *  current es incorrecta (INVALID_PASSWORD, code 4005). La sesion sigue
   *  viva porque el backend preserva la sesion actual. */
  changePassword: (data: ChangePasswordPayload) =>
    apiFetch<Envelope<{ ok: boolean }>>('/users', {
      method: 'POST',
      body: { operation: 'profile', action: 'change-password', data },
    }),

  /** profile.delete-account: soft-delete. Exige el sentinel
   *  'DELETE-MY-ACCOUNT'. 409 CANNOT_DELETE_ADMIN_ACCOUNT si el user es admin. */
  deleteAccount: (data: DeleteAccountPayload) =>
    apiFetch<Envelope<{ ok: boolean }>>('/users', {
      method: 'POST',
      body: { operation: 'profile', action: 'delete-account', data },
    }),
}
