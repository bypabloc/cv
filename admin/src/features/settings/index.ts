/**
 * @module features/settings
 * @description Barrel publico del feature settings (gestion total de la cuenta
 *   del usuario autenticado). Export explicito (no `export *`). Compone el
 *   Lambda `users` (operation `profile`) + los hooks/componentes MFA/WebAuthn
 *   que aporta el feature `auth` (su unica dependencia cross-feature).
 */

// Componentes
export { ChangeEmailForm } from './components/change-email-form'
export { ChangePasswordForm } from './components/change-password-form'
export { ConfirmEmailChange } from './components/confirm-email-change'
export { DeleteAccountSection } from './components/delete-account-section'
export { EmailCodeSection } from './components/email-code-section'
export { MfaMethodsList } from './components/mfa-methods-list'
export { ProfileForm } from './components/profile-form'
export { RecoveryCodesSection } from './components/recovery-codes-section'
export { WebAuthnCredentialsList } from './components/webauthn-credentials-list'
// Hooks
export {
  useChangeEmailInitiate,
  useConfirmEmailChange,
} from './hooks/use-change-email'
export { useChangePassword } from './hooks/use-change-password'
export { useDeleteAccount } from './hooks/use-delete-account'
export { useProfile } from './hooks/use-profile'
export { useUpdateProfile } from './hooks/use-update-profile'
// Tipos publicos
export type {
  ChangeEmailPayload,
  ChangePasswordPayload,
  ConfirmEmailChangePayload,
  DeleteAccountPayload,
  UpdateProfilePayload,
} from './types'
