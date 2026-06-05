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
	/** El backend lo emite al cerrar el login (checklist completo). Opcional:
	 *  algunos cierres del checklist no re-envian el perfil. */
	user?: User;
	/** Marcador del backend nuevo: true cuando el login quedo completo. */
	mfa_complete?: boolean;
	token_type?: string;
}

/** Flujo multi-step (register/login). `methods` aparece con MFA. */
export interface TempTokenResponse {
	temp_token: string;
	user_id?: string;
	expires_in?: number;
	methods?: ("magic-link" | "email-code" | "password" | "totp" | "webauthn")[];
	/** Paso del flujo (0 precheck, 1 passwordless, 2 step-up MFA). */
	step?: number;
	/** Marcador del backend nuevo: false mientras el login NO esta completo. */
	mfa_complete?: boolean;
	/** Solo en login.start del alta fusionada: true si el email fue creado. */
	created?: boolean;
}

/**
 * Tipo de metodo `required` que el user marco para su login (checklist). El
 * orden de `methods_required` que devuelve login.check-email es fijo:
 * password, passwordless, totp, email_code, webauthn.
 */
export type MethodKind =
	| "password"
	| "passwordless"
	| "totp"
	| "email_code"
	| "webauthn";

/**
 * Un metodo del checklist de login. `dispatch_action` es la action que el
 * front debe invocar; `sent` indica si el email-code/passwordless ya se envio
 * (null cuando el metodo no requiere envio previo).
 */
export interface MethodRequired {
	type: MethodKind;
	input: "password" | "code6" | "code8" | "email" | "webauthn";
	sent: boolean | null;
	dispatch_action: string;
}

/**
 * Resultado de cualquier verify del checklist. Se discrimina por
 * `mfa_complete` / la presencia de `access_token`: AuthResponse cierra el
 * login (tokens), TempTokenResponse rota el temp_token y deja metodos
 * pendientes.
 */
export type VerifyResult = AuthResponse | TempTokenResponse;

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

/**
 * login.check-email — banderas del email + el precheck + (backend nuevo) la
 * lista de metodos `required` que el user marco. Para un user ACTIVE,
 * `methods_required` trae al menos 1 entrada y define el checklist de login.
 * unavailable no trae `temp_token`; exists:false/pending no traen
 * `methods_required` (alta / passwordless por el flujo viejo).
 */
export interface CheckEmailResponse {
	exists: boolean;
	has_password?: boolean;
	pending?: boolean;
	unavailable?: boolean;
	/**
	 * Temp JWT precheck (flow='login' step=0) que autoriza login.start.
	 * Presente salvo en el caso `unavailable` (no hay flujo que continuar).
	 * login.start lo manda en `Authorization: Bearer` en vez de Turnstile.
	 */
	temp_token?: string;
	/** Metodos `required` del user ACTIVE; define el checklist de login. */
	methods_required?: MethodRequired[];
}
