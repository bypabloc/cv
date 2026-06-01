import type {
  AuthenticationResponseJSON,
  RegistrationResponseJSON,
} from '@simplewebauthn/browser'
import { apiFetch } from '@/lib/api-client'
import type {
  AuthResponse,
  Envelope,
  MfaListResponse,
  RecoveryCodesResponse,
  RefreshResponse,
  TempTokenResponse,
  TotpSetupResponse,
  WebauthnCredentialsResponse,
  WebauthnLoginOptionsResponse,
  WebauthnRegisterOptionsResponse,
} from '@/types/api'
import type { MfaKind } from '@/types/models'

/**
 * @module features/auth/api/auth-client
 * @description Cliente tipado del Lambda `auth` (6 operations / 26 actions).
 *   Todas las actions hacen `POST /auth` con body JSON `{operation, action,
 *   data}` y respuesta envuelta en `{is_valid, code, data}`.
 *
 * Auth por action:
 * - register / login / verify / session.refresh -> `skipAuth: true` (sin sesion).
 * - session.refresh -> ademas `skipRefresh: true` (NUNCA entra al mutex).
 * - mfa.* y webauthn.* -> con access JWT (Bearer), salvo
 *   `mfa.recovery-codes-consume` (temp JWT step=2, skipAuth) y
 *   `webauthn.login-options` / `webauthn.login-verify` (login sin sesion).
 *
 * Los `verify-magic-link` (register/login) son callbacks GET resueltos en
 * `(auth)/callback`; NO se exponen como funciones aqui.
 */
export const authClient = {
  // --- operation register (3 actions; verify-magic-link es callback GET) ---

  /** register.start: dispara el envio de magic-link + code al email. */
  registerStart: (data: {
    email: string
    cf_turnstile_response: string
    niche?: string
  }) =>
    apiFetch<Envelope<TempTokenResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'register', action: 'start', data },
    }),

  /** register.verify-code: cierra el register con el code de 8 chars. */
  registerVerifyCode: (data: { code: string; temp_token: string }) =>
    apiFetch<Envelope<AuthResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'register', action: 'verify-code', data },
    }),

  // --- operation login (5 actions; verify-magic-link es callback GET) ---

  /** login.start: 200 TempTokenResponse (con methods) / 404 EMAIL_NOT_FOUND. */
  loginStart: (data: {
    email: string
    cf_turnstile_response: string
    password?: string
    niche?: string
  }) =>
    apiFetch<Envelope<TempTokenResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'login', action: 'start', data },
    }),

  /** login.verify-code: cierra el login con el code de 8 chars. */
  loginVerifyCode: (data: { code: string; temp_token: string }) =>
    apiFetch<Envelope<AuthResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'login', action: 'verify-code', data },
    }),

  /**
   * login.verify-password: valida password (argon2). Sin MFA cierra con
   * AuthResponse; con MFA devuelve un temp JWT step=2 + `methods`.
   */
  loginVerifyPassword: (data: { temp_token: string; password: string }) =>
    apiFetch<Envelope<AuthResponse | TempTokenResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'login', action: 'verify-password', data },
    }),

  /** login.verify-totp: paso final del login con MFA TOTP (temp step=2). */
  loginVerifyTotp: (data: { code: string; temp_token: string }) =>
    apiFetch<Envelope<AuthResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'login', action: 'verify-totp', data },
    }),

  // --- operation verify (2 actions) ---

  /** verify.set-password: setea password en el onboarding (temp step>=2). */
  setPassword: (data: { password: string; temp_token: string }) =>
    apiFetch<Envelope<AuthResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'verify', action: 'set-password', data },
    }),

  /** verify.resend-code: reenvia el code (rate-limit propio). */
  resendCode: (data: { temp_token: string }) =>
    apiFetch<Envelope<{ ok: true }>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'verify', action: 'resend-code', data },
    }),

  // --- operation session (2 actions) ---

  /** session.refresh: rota la familia. skipRefresh para no recursar el mutex. */
  sessionRefresh: (data: { refresh_token: string }) =>
    apiFetch<Envelope<RefreshResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      skipRefresh: true,
      body: { operation: 'session', action: 'refresh', data },
    }),

  /** session.logout: blacklistea la familia en el backend. */
  sessionLogout: () =>
    apiFetch<Envelope<{ ok: true }>>('/auth', {
      method: 'POST',
      body: { operation: 'session', action: 'logout', data: {} },
    }),

  // --- operation mfa (8 actions) ---

  /** mfa.setup-totp: devuelve secret_b32 + otpauth_url (el front pinta el QR). */
  mfaSetupTotp: () =>
    apiFetch<Envelope<TotpSetupResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'mfa', action: 'setup-totp', data: {} },
    }),

  /** mfa.confirm-totp: cierra el setup (primer metodo MFA revoca la familia). */
  mfaConfirmTotp: (data: { code: string }) =>
    apiFetch<Envelope<MfaListResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'mfa', action: 'confirm-totp', data },
    }),

  /** mfa.setup-email-code: activa MFA via email-code. */
  mfaSetupEmailCode: () =>
    apiFetch<Envelope<MfaListResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'mfa', action: 'setup-email-code', data: {} },
    }),

  /** mfa.set-preferred: marca el metodo preferido. */
  mfaSetPreferred: (data: { kind: MfaKind }) =>
    apiFetch<Envelope<MfaListResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'mfa', action: 'set-preferred', data },
    }),

  /** mfa.disable: 409 si dejaria total_mfa == 0 (MUST_KEEP_ONE_MFA_METHOD). */
  mfaDisable: (data: { kind: MfaKind }) =>
    apiFetch<Envelope<MfaListResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'mfa', action: 'disable', data },
    }),

  /** mfa.list: estado actual de los metodos MFA. */
  mfaList: () =>
    apiFetch<Envelope<MfaListResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'mfa', action: 'list', data: {} },
    }),

  /** mfa.recovery-codes-generate: 10 codes mostrados UNA sola vez. */
  mfaRecoveryCodesGenerate: () =>
    apiFetch<Envelope<RecoveryCodesResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'mfa', action: 'recovery-codes-generate', data: {} },
    }),

  /**
   * mfa.recovery-codes-consume: consume un recovery code en el login con MFA.
   * Exige temp JWT step=2 (factor fuerte) -> skipAuth + temp_token. 403
   * RECOVERY_REQUIRES_STRONG_FACTOR si el temp viene de magic-link/email-code.
   */
  mfaRecoveryCodesConsume: (data: { code: string; temp_token: string }) =>
    apiFetch<Envelope<AuthResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'mfa', action: 'recovery-codes-consume', data },
    }),

  // --- operation webauthn (6 actions) ---

  /** webauthn.register-options: challenge_id + options (TTL 5 min en DDB). */
  webauthnRegisterOptions: () =>
    apiFetch<Envelope<WebauthnRegisterOptionsResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'webauthn', action: 'register-options', data: {} },
    }),

  /** webauthn.register-verify: cierra el registro de un passkey. */
  webauthnRegisterVerify: (data: {
    challenge_id: string
    response: RegistrationResponseJSON
    nickname?: string
  }) =>
    apiFetch<Envelope<MfaListResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'webauthn', action: 'register-verify', data },
    }),

  /** webauthn.login-options: passkey login passwordless (sin sesion). */
  webauthnLoginOptions: (data: { email: string }) =>
    apiFetch<Envelope<WebauthnLoginOptionsResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'webauthn', action: 'login-options', data },
    }),

  /** webauthn.login-verify: cierra el login passwordless. 401 si clone. */
  webauthnLoginVerify: (data: {
    challenge_id: string
    response: AuthenticationResponseJSON
  }) =>
    apiFetch<Envelope<AuthResponse>>('/auth', {
      method: 'POST',
      skipAuth: true,
      body: { operation: 'webauthn', action: 'login-verify', data },
    }),

  /** webauthn.list-credentials: passkeys del usuario. */
  webauthnListCredentials: () =>
    apiFetch<Envelope<WebauthnCredentialsResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'webauthn', action: 'list-credentials', data: {} },
    }),

  /** webauthn.delete-credential: 409 si MUST_KEEP_ONE_MFA_METHOD. */
  webauthnDeleteCredential: (data: { credential_id: string }) =>
    apiFetch<Envelope<WebauthnCredentialsResponse>>('/auth', {
      method: 'POST',
      body: { operation: 'webauthn', action: 'delete-credential', data },
    }),
}
