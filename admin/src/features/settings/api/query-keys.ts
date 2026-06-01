/**
 * @module features/settings/api/query-keys
 * @description Query keys estructurados de Tanstack Query para el dominio
 *   settings (perfil del usuario). Las mutations invalidan estas keys; las
 *   queries las consumen. MFA/WebAuthn usan las keys del feature auth.
 */
export const settingsKeys = {
	all: ["settings"] as const,
	profile: () => [...settingsKeys.all, "profile"] as const,
};
