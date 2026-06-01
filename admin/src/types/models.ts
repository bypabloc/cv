/**
 * @module types/models
 * @description Domain types del admin, derivados del contrato real de los
 *   Lambdas `auth` y `users` (serverless/lambda/services/{auth,users}/).
 */

export type UserStatus =
	| "pending"
	| "active"
	| "disabled"
	| "locked"
	| "deleted";

export type MfaKind = "totp" | "email_code";

export interface User {
	id: string;
	email: string;
	status: UserStatus;
	display_name?: string | null;
	has_password: boolean;
	mfa_methods: ("totp" | "webauthn" | "email_code")[];
}

/** Perfil completo (users.profile.get). El backend devuelve `id`. */
export interface UserProfile {
	id: string;
	email: string;
	display_name: string | null;
	status: UserStatus;
	locale?: "es" | "en" | null;
	timezone?: string | null;
	marketing_consent?: boolean | null;
	created_at?: string;
}

export interface MfaMethod {
	kind: MfaKind;
	confirmed_at: string | null;
	is_preferred: boolean;
}

export interface WebauthnCredential {
	id: string;
	nickname: string | null;
	last_used_at: string | null;
	created_at: string;
}

/** Sesion de la cuenta auth (users.status.list-sessions). */
export interface AccountSession {
	session_id: string;
	family_id: string;
	ip: string | null;
	user_agent: string | null;
	created_at: string;
	last_seen_at: string | null;
	is_current: boolean;
}

export interface AccountStatus {
	user_id: string;
	status: UserStatus;
	current_session_id: string;
}

/** Usuario en el listado admin (users.admin.list-users / get-user). */
export interface AdminUser {
	user_id: string;
	email: string;
	display_name: string | null;
	status: UserStatus;
	created_at: string;
	total_mfa: number;
}

export interface AdminAction {
	action_id: string;
	actor_user_id: string;
	target_user_id: string | null;
	action: string;
	created_at: string;
}
