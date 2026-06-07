import type {
	AuthenticationResponseJSON,
	RegistrationResponseJSON,
} from "@simplewebauthn/browser";
import { apiFetch } from "@/lib/api-client";
import type {
	AuthResponse,
	CheckEmailResponse,
	Envelope,
	MfaListResponse,
	RecoveryCodesResponse,
	RefreshResponse,
	SecurityOverviewResponse,
	TempTokenResponse,
	TotpSetupResponse,
	VerifyResult,
	WebauthnCredentialsResponse,
	WebauthnLoginOptionsResponse,
	WebauthnRegisterOptionsResponse,
} from "@/types/api";
import type { MfaKind } from "@/types/models";

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
	// --- operation login (5 actions; verify-magic-link es callback GET) ---

	/**
	 * login.check-email: pre-chequeo del email antes de iniciar el flujo.
	 * Devuelve banderas (exists, has_password, pending, unavailable) + el
	 * `temp_token` precheck, NO la lista de metodos. Sin sesion (skipAuth) +
	 * exige Turnstile (UNICO punto del flujo de login con captcha).
	 */
	loginCheckEmail: (data: { email: string; cf_turnstile_response: string }) =>
		apiFetch<Envelope<CheckEmailResponse>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "login", action: "check-email", data },
		}),

	/**
	 * login.start: resuelve el user por el `sub` del precheck. Para un user
	 * EXISTENTE NO manda email (el body solo lleva `{operation, action}`);
	 * para un email NUEVO (alta fusionada) SI manda `{email}`. Devuelve un
	 * temp_token (step=2 con `methods` para un user ACTIVE; step=1 con
	 * methods:['passwordless'] para alta/pending). `created` indica si el
	 * email fue CREADO.
	 *
	 * Ya NO valida Turnstile: el captcha se resuelve una sola vez en
	 * login.check-email, que emite el `precheckToken` (temp JWT flow='login'
	 * step=0). login.start lo EXIGE en `Authorization: Bearer`; sin el -> 401
	 * MISSING_PRECHECK. `skipAuth: true` evita que apiFetch inyecte el access
	 * token del store; el header lo seteamos a mano con el precheck.
	 */
	loginStart: (precheckToken: string, email?: string) =>
		apiFetch<Envelope<TempTokenResponse>>("/auth", {
			method: "POST",
			skipAuth: true,
			headers: { Authorization: `Bearer ${precheckToken}` },
			body: {
				operation: "login",
				action: "start",
				data: email === undefined ? {} : { email },
			},
		}),

	/**
	 * login.send-email-code: dispara el envio del code de 8 chars al email del
	 * user (paso previo del metodo email_code / passwordless del checklist).
	 */
	loginSendEmailCode: (data: { temp_token: string }) =>
		apiFetch<Envelope<{ ok: true }>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "login", action: "send-email-code", data },
		}),

	/**
	 * login.verify-code: valida el code de 8 chars. Devuelve VerifyResult:
	 * AuthResponse si cierra el login, o un temp_token nuevo (rolling) con los
	 * metodos pendientes si quedan factores por completar.
	 */
	loginVerifyCode: (data: { code: string; temp_token: string }) =>
		apiFetch<Envelope<VerifyResult>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "login", action: "verify-code", data },
		}),

	/**
	 * login.verify-password: valida password (argon2). Devuelve VerifyResult:
	 * AuthResponse si cierra el login, o un temp_token nuevo (rolling) +
	 * `methods` pendientes si quedan factores por completar.
	 */
	loginVerifyPassword: (data: { temp_token: string; password: string }) =>
		apiFetch<Envelope<VerifyResult>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "login", action: "verify-password", data },
		}),

	/**
	 * login.verify-totp: valida el code TOTP (6 digitos). Devuelve VerifyResult:
	 * AuthResponse si cierra el login, o un temp_token nuevo (rolling) +
	 * `methods` pendientes si quedan factores por completar.
	 */
	loginVerifyTotp: (data: { code: string; temp_token: string }) =>
		apiFetch<Envelope<VerifyResult>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "login", action: "verify-totp", data },
		}),

	// --- operation verify (2 actions) ---

	/** verify.set-password: setea password en el onboarding (temp step>=2). */
	setPassword: (data: { password: string; temp_token: string }) =>
		apiFetch<Envelope<AuthResponse>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "verify", action: "set-password", data },
		}),

	/** verify.resend-code: reenvia el code (rate-limit propio). */
	resendCode: (data: { temp_token: string }) =>
		apiFetch<Envelope<{ ok: true }>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "verify", action: "resend-code", data },
		}),

	// --- operation session (2 actions) ---

	/** session.refresh: rota la familia. skipRefresh para no recursar el mutex. */
	sessionRefresh: (data: { refresh_token: string }) =>
		apiFetch<Envelope<RefreshResponse>>("/auth", {
			method: "POST",
			skipAuth: true,
			skipRefresh: true,
			body: { operation: "session", action: "refresh", data },
		}),

	/** session.logout: blacklistea la familia en el backend. */
	sessionLogout: () =>
		apiFetch<Envelope<{ ok: true }>>("/auth", {
			method: "POST",
			body: { operation: "session", action: "logout", data: {} },
		}),

	// --- operation mfa (8 actions) ---

	/** mfa.setup-totp: devuelve secret_b32 + otpauth_url (el front pinta el QR). */
	mfaSetupTotp: () =>
		apiFetch<Envelope<TotpSetupResponse>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "setup-totp", data: {} },
		}),

	/** mfa.confirm-totp: cierra el setup (primer metodo MFA revoca la familia). */
	mfaConfirmTotp: (data: { code: string }) =>
		apiFetch<Envelope<MfaListResponse>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "confirm-totp", data },
		}),

	/** mfa.setup-email-code: activa MFA via email-code. */
	mfaSetupEmailCode: () =>
		apiFetch<Envelope<MfaListResponse>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "setup-email-code", data: {} },
		}),

	/** mfa.set-preferred: marca el metodo preferido. */
	mfaSetPreferred: (data: { kind: MfaKind }) =>
		apiFetch<Envelope<MfaListResponse>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "set-preferred", data },
		}),

	/** mfa.disable: 409 si dejaria total_mfa == 0 (MUST_KEEP_ONE_MFA_METHOD). */
	mfaDisable: (data: { kind: MfaKind }) =>
		apiFetch<Envelope<MfaListResponse>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "disable", data },
		}),

	/** mfa.list: estado actual de los metodos MFA. */
	mfaList: () =>
		apiFetch<Envelope<MfaListResponse>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "list", data: {} },
		}),

	/** mfa.recovery-codes-generate: 10 codes mostrados UNA sola vez. */
	mfaRecoveryCodesGenerate: () =>
		apiFetch<Envelope<RecoveryCodesResponse>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "recovery-codes-generate", data: {} },
		}),

	/**
	 * mfa.recovery-codes-consume: consume un recovery code en el login con MFA.
	 * Exige temp JWT step=2 (factor fuerte) -> skipAuth + temp_token. 403
	 * RECOVERY_REQUIRES_STRONG_FACTOR si el temp viene de magic-link/email-code.
	 */
	mfaRecoveryCodesConsume: (data: { code: string; temp_token: string }) =>
		apiFetch<Envelope<AuthResponse>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "mfa", action: "recovery-codes-consume", data },
		}),

	// --- operation webauthn (6 actions) ---

	/** webauthn.register-options: challenge_id + options (TTL 5 min en DDB). */
	webauthnRegisterOptions: () =>
		apiFetch<Envelope<WebauthnRegisterOptionsResponse>>("/auth", {
			method: "POST",
			body: { operation: "webauthn", action: "register-options", data: {} },
		}),

	/** webauthn.register-verify: cierra el registro de un passkey. */
	webauthnRegisterVerify: (data: {
		challenge_id: string;
		response: RegistrationResponseJSON;
		nickname?: string;
	}) =>
		apiFetch<Envelope<MfaListResponse>>("/auth", {
			method: "POST",
			body: { operation: "webauthn", action: "register-verify", data },
		}),

	/** webauthn.login-options: passkey login passwordless (sin sesion). */
	webauthnLoginOptions: (data: { email: string }) =>
		apiFetch<Envelope<WebauthnLoginOptionsResponse>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "webauthn", action: "login-options", data },
		}),

	/**
	 * webauthn.login-verify: valida la assertion del passkey. Devuelve
	 * VerifyResult: AuthResponse si cierra el login (passwordless), o un
	 * temp_token nuevo (rolling) + `methods` pendientes cuando el passkey es un
	 * factor del checklist. 401 si clone (sign_count regresivo).
	 */
	webauthnLoginVerify: (data: {
		challenge_id: string;
		response: AuthenticationResponseJSON;
		temp_token?: string;
	}) =>
		apiFetch<Envelope<VerifyResult>>("/auth", {
			method: "POST",
			skipAuth: true,
			body: { operation: "webauthn", action: "login-verify", data },
		}),

	/** webauthn.list-credentials: passkeys del usuario. */
	webauthnListCredentials: () =>
		apiFetch<Envelope<WebauthnCredentialsResponse>>("/auth", {
			method: "POST",
			body: { operation: "webauthn", action: "list-credentials", data: {} },
		}),

	/** webauthn.delete-credential: 409 si MUST_KEEP_ONE_MFA_METHOD. */
	webauthnDeleteCredential: (data: { credential_id: string }) =>
		apiFetch<Envelope<WebauthnCredentialsResponse>>("/auth", {
			method: "POST",
			body: { operation: "webauthn", action: "delete-credential", data },
		}),

	// --- operation security (overview consolidado) ---

	/** security.overview: estado de los 5 metodos (authed, sin payload). */
	securityOverview: () =>
		apiFetch<Envelope<SecurityOverviewResponse>>("/auth", {
			method: "POST",
			body: { operation: "security", action: "overview", data: {} },
		}),

	/** mfa.enable: activa (soft-enable) un metodo MFA por kind. 204. */
	mfaEnable: (data: { kind: MfaKind }) =>
		apiFetch<Envelope<unknown>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "enable", data },
		}),

	/** mfa.set-required: marca/desmarca un metodo MFA como requerido. 204. */
	mfaSetRequired: (data: { kind: MfaKind; required: boolean }) =>
		apiFetch<Envelope<unknown>>("/auth", {
			method: "POST",
			body: { operation: "mfa", action: "set-required", data },
		}),

	/** webauthn.enable: re-activa (soft-enable) un passkey por credential_id. 204. */
	webauthnEnable: (data: { credential_id: string }) =>
		apiFetch<Envelope<unknown>>("/auth", {
			method: "POST",
			body: { operation: "webauthn", action: "enable", data },
		}),

	/** webauthn.disable: soft-disable reversible. 409 MUST_KEEP_ONE_MFA_METHOD. */
	webauthnDisable: (data: { credential_id: string }) =>
		apiFetch<Envelope<unknown>>("/auth", {
			method: "POST",
			body: { operation: "webauthn", action: "disable", data },
		}),

	/** webauthn.set-required: marca/desmarca un passkey como requerido. 204. */
	webauthnSetRequired: (data: { credential_id: string; required: boolean }) =>
		apiFetch<Envelope<unknown>>("/auth", {
			method: "POST",
			body: { operation: "webauthn", action: "set-required", data },
		}),
};
