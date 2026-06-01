/**
 * @module features/settings/types
 * @description Payloads del feature settings, derivados del contrato real del
 *   Lambda `users` (operation `profile`). Los responses (UserProfile, etc.)
 *   viven en `@/types/{api,models}` (singleton del backend). TypeScript strict.
 */

/** users.profile.update — la UI principal edita display_name. */
export interface UpdateProfilePayload {
  display_name: string
}

/** users.profile.change-email — inicia el flow de cambio de email. */
export interface ChangeEmailPayload {
  new_email: string
}

/** users.profile.confirm-email-change — cierra el flow con el token. */
export interface ConfirmEmailChangePayload {
  token: string
}

/** users.profile.change-password — action REAL, validada con el access JWT. */
export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

/**
 * users.profile.delete-account — el backend exige el sentinel string EXACTO
 * 'DELETE-MY-ACCOUNT' (NO confirm:true).
 */
export interface DeleteAccountPayload {
  confirm: 'DELETE-MY-ACCOUNT'
}
