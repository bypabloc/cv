import type {
	AccountSession,
	AccountStatus,
	AdminAction,
	AdminUser,
	MfaMethod,
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

/** users.profile.get / update */
export interface ProfileResponse {
	profile: UserProfile;
}

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
