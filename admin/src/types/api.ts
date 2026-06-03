import type {
	AccountSession,
	AccountStatus,
	AdminAction,
	AdminUser,
	MfaMethod,
	SecurityMethod,
	User,
	UserProfile,
	WebauthnCredential,
} from "./models";

/**
 * @module types/api
 * @description Tipos de respuestas tipadas de los Lambdas `auth` y `users`.
 *   Los Lambdas envuelven el payload util en `{ is_valid, code, data }`.
 */

/** Envelope estandar del backend serverless. */
export interface Envelope<T> {
	is_valid: boolean;
	code: number;
	data: T;
}

/** access + refresh + user emitidos al cerrar register/login. */
export interface AuthResponse {
	access_token: string;
	refresh_token: string;
	expires_in: number;
	user: User;
}

/** Flujo multi-step (register/login). `methods` aparece con MFA. */
export interface TempTokenResponse {
	temp_token: string;
	user_id: string;
	expires_in: number;
	methods?: ("magic-link" | "email-code" | "password" | "totp" | "webauthn")[];
}

export interface RefreshResponse {
	access_token: string;
	refresh_token: string;
	expires_in: number;
}

export interface MfaListResponse {
	methods: MfaMethod[];
	webauthn_count: number;
	total_mfa: number;
}

/** El front renderiza el QR desde `otpauth_url`; no llega imagen. */
export interface TotpSetupResponse {
	secret_b32: string;
	otpauth_url: string;
}

export interface RecoveryCodesResponse {
	codes: string[];
}

export interface WebauthnRegisterOptionsResponse {
	challenge_id: string;
	options: import("@simplewebauthn/browser").PublicKeyCredentialCreationOptionsJSON;
}

export interface WebauthnLoginOptionsResponse {
	challenge_id: string;
	options: import("@simplewebauthn/browser").PublicKeyCredentialRequestOptionsJSON;
}

export interface WebauthnCredentialsResponse {
	credentials: WebauthnCredential[];
}

/** users.profile.get / update — el backend responde el perfil FLAT (los
 *  campos de UserProfile al nivel raiz del `data`, NO anidados en `profile`),
 *  igual que el resto de las 26 actions (ver shared.lambda_kit.http_dispatch,
 *  json_response(status, result.data)). */
export type ProfileResponse = UserProfile;

/** users.status.get */
export type StatusResponse = AccountStatus;

/** users.status.list-sessions */
export interface SessionsResponse {
	sessions: AccountSession[];
}

/** users.admin.list-users */
export interface ListUsersResponse {
	users: AdminUser[];
	page: number;
	page_size: number;
	total: number;
}

/** users.admin.list-admin-actions */
export interface AdminActionsResponse {
	actions: AdminAction[];
}

/** security.overview — 5 entradas (totp, email_code, webauthn, recovery_codes,
 *  password) con su estado de configuracion / enabled / required / preferred. */
export interface SecurityOverviewResponse {
	methods: SecurityMethod[];
}

/** login.check-email — NO devuelve la lista de metodos, solo banderas. */
export interface CheckEmailResponse {
	exists: boolean;
	has_password?: boolean;
	pending?: boolean;
	unavailable?: boolean;
}
