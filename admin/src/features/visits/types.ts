/**
 * @module features/visits/types
 * @description Shapes de las respuestas del Lambda `analytics` (operation
 *   `visits`): list (paginado) y landing-pages (ranking agregado). Espejan el
 *   `data` que devuelve cada endpoint.
 */

import type { DateRangeParams } from "@/features/analytics/types";

/** visits/list — params del listado paginado. Requiere `offset`. */
export interface VisitsListParams extends DateRangeParams {
	page?: number;
	page_size?: number;
	offset?: number;
	niche?: string;
	country?: string;
}

/** Una fila del listado de visitas. */
export interface VisitRow {
	visit_id: string;
	session_id: string;
	started_at: string;
	ended_at: string | null;
	event_count: number;
	ip: string | null;
	country: string | null;
	utm_source: string | null;
	utm_medium: string | null;
	utm_campaign: string | null;
	referrer: string | null;
	landing_page_path: string | null;
	niche: string | null;
}

/** visits/list — pagina de visitas. */
export interface VisitsListResponse {
	items: VisitRow[];
	page: number;
	page_size: number;
	total: number;
	has_more: boolean;
}

/** visits/landing-pages — params del ranking de landing pages. */
export interface LandingPagesParams extends DateRangeParams {
	limit?: number;
}

/** Una landing page rankeada. */
export interface LandingPageItem {
	landing_page_path: string;
	visits: number;
	unique_visitors: number;
}

/** visits/landing-pages — ranking de landing pages. */
export interface LandingPagesResponse {
	items: LandingPageItem[];
}
