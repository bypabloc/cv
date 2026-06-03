/**
 * @module routes
 * @description Constantes de paths del admin. Las pages NUNCA hardcodean
 *   strings de ruta: importan de aqui. El slot `metrics` es la raiz del
 *   area de metricas que monta el plan b-analytics-api.
 */
export const ROUTES = {
	home: "/",
	auth: {
		login: "/login",
		verify: "/verify",
		callback: "/auth/callback",
		setPassword: "/set-password",
	},
	admin: {
		root: "/",
		metrics: "/metrics",
		// Area de metricas del visitante (Lambda analytics). Todo bajo
		// /metrics/* para NO colisionar con /sessions (Mis sesiones de auth).
		metricsTimeseries: "/metrics/timeseries",
		metricsSessions: "/metrics/sessions",
		metricsSessionDetail: (id: string) =>
			`/metrics/sessions/detail?id=${encodeURIComponent(id)}`,
		metricsEvents: "/metrics/events",
		metricsVisits: "/metrics/visits",
		metricsGeo: "/metrics/geo",
		metricsDevices: "/metrics/devices",
		metricsFunnel: "/metrics/funnel",
		metricsContacts: "/metrics/contacts",
		settings: "/settings",
		settingsSecurity: "/settings/security",
		sessions: "/sessions",
		users: "/users",
		cv: "/cv",
	},
} as const;

/** @function loginWithNext — construye /login?next=<path> URL-encoded. */
export function loginWithNext(next: string): string {
	return `${ROUTES.auth.login}?next=${encodeURIComponent(next)}`;
}
