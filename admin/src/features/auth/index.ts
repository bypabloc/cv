/**
 * @module features/auth
 * @description Barrel publico del feature auth. Export explicito (no `export *`)
 *   de los componentes, hooks y store que consumen las pages y otros features.
 */

// Tipos publicos
export type {
	AuthResponse,
	CheckEmailResponse,
	MfaListResponse,
	RecoveryCodesResponse,
	SecurityOverviewResponse,
	TempTokenResponse,
	TotpSetupResponse,
	WebauthnCredentialsResponse,
} from "@/types/api";
// Componentes
export { AuthGuard } from "./components/auth-guard";
export { LoginForm } from "./components/login-form";
export { LoginPasswordInput } from "./components/login-password-input";
export { LoginTotpInput } from "./components/login-totp-input";
export { MagicLinkPrompt } from "./components/magic-link-prompt";
export { RecoveryCodeInput } from "./components/recovery-code-input";
export { RecoveryCodesModal } from "./components/recovery-codes-modal";
export { SetPasswordForm } from "./components/set-password-form";
export { TotpSetup } from "./components/totp-setup";
export { TurnstileWidget } from "./components/turnstile-widget";
export { VerifyCodeInput } from "./components/verify-code-input";
export { WebAuthnLoginButton } from "./components/webauthn-login-button";
export { WebAuthnRegisterButton } from "./components/webauthn-register-button";
// Hooks de gestion (consumidos por el feature settings)
export { useCheckEmail } from "./hooks/use-check-email";
export { useConfirmTotp } from "./hooks/use-confirm-totp";
export { useDeleteCredential } from "./hooks/use-delete-credential";
export { useDisableMfa } from "./hooks/use-disable-mfa";
export { useGenerateRecoveryCodes } from "./hooks/use-generate-recovery-codes";
export { useListCredentials } from "./hooks/use-list-credentials";
export { useLogout } from "./hooks/use-logout";
export { useMfaList } from "./hooks/use-mfa-list";
export { useSetPreferredMfa } from "./hooks/use-set-preferred-mfa";
export { useSetupEmailCode } from "./hooks/use-setup-email-code";
export { useSetupTotp } from "./hooks/use-setup-totp";
export { useWebauthnRegisterOptions } from "./hooks/use-webauthn-register-options";
export { useWebauthnRegisterVerify } from "./hooks/use-webauthn-register-verify";
// Store
export { useAuthStore } from "./store/use-auth-store";
