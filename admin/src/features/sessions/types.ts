/**
 * @module features/sessions/types
 * @description Shapes de las respuestas del Lambda `analytics` (operation
 *   `sessions`): tracking de VISITANTES (NO `sessions-mgmt` de auth). Espejan
 *   el `data` que devuelve cada endpoint (list paginado + detail). Es PII, por
 *   eso el queryKey[1] === 'sessions' queda excluido del persister.
 */

/** Una fila de la lista de sesiones de visitantes (sessions/list). */
export interface SessionRow {
	session_id: string;
	first_seen_at: string;
	last_seen_at: string;
	browser: string;
	browser_version: string;
	os: string;
	device_type: string;
	visits_count: number;
}

/** sessions/list — listado paginado de sesiones (PII, staleTime 30s). */
export interface SessionListResponse {
	items: SessionRow[];
	page: number;
	page_size: number;
	total: number;
	has_more: boolean;
}

/** Params del listado paginado de sesiones (con filtros opcionales). */
export interface SessionListParams {
	from?: string;
	to?: string;
	page?: number;
	page_size?: number;
	device_type?: string;
	browser?: string;
}

/** Una visita asociada a una sesion (sessions/detail). */
export interface VisitRow {
	visit_id: string;
	started_at: string;
	ended_at: string;
	event_count: number;
	ip: string;
	country: string;
	utm_source: string;
	utm_medium: string;
	utm_campaign: string;
	referrer: string;
	landing_page_path: string;
	niche: string;
}

/** sessions/detail — sesion + sus visitas + total de eventos (staleTime 0). */
export interface SessionDetailResponse {
	session: SessionRow;
	visits: VisitRow[];
	events_count: number;
}

/** Params del detalle de una sesion. */
export interface SessionDetailParams {
	session_id: string;
}
