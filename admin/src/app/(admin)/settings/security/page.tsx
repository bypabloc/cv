'use client'

import {
  ChangePasswordForm,
  EmailCodeSection,
  MfaMethodsList,
  RecoveryCodesSection,
  WebAuthnCredentialsList,
} from '@/features/settings'

/**
 * @page SecuritySettingsPage
 * @description Seguridad de la cuenta: cambio de contrasena (action REAL),
 *   metodos MFA (TOTP + email-code), passkeys WebAuthn y codigos de
 *   recuperacion. Compone el feature `auth` via el feature `settings`.
 */
export default function SecuritySettingsPage() {
  return (
    <section className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold">Seguridad</h1>

      <ChangePasswordForm />
      <MfaMethodsList />
      <EmailCodeSection />
      <WebAuthnCredentialsList />
      <RecoveryCodesSection />
    </section>
  )
}
