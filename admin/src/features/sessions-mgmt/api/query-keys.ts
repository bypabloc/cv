/**
 * @module features/sessions-mgmt/api/query-keys
 * @description Query keys estructurados de Tanstack Query para las sesiones de
 *   la cuenta auth. Las mutations invalidan estas keys; las queries las
 *   consumen.
 */
export const sessionsKeys = {
	all: ["status"] as const,
	status: () => [...sessionsKeys.all, "get"] as const,
	sessions: () => [...sessionsKeys.all, "list-sessions"] as const,
};
