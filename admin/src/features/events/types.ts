/**
 * @module features/events/types
 * @description Shapes de las respuestas del Lambda `analytics` (operation
 *   `events`): distribution, list, heatmap. Espejan el `data` que devuelve
 *   cada endpoint.
 */

import type { DateRangeParams } from "@/features/analytics/types";

export type { DateRangeParams };

/** Una fila del ranking de tipos de evento (events/distribution). */
export interface EventDistributionItem {
	event_type: string;
	count: number;
	pct: number;
}

/** events/distribution — ranking de tipos de evento por frecuencia. */
export interface EventDistributionResponse {
	items: EventDistributionItem[];
}

/** Una fila cruda de evento (events/list). */
export interface EventRow {
	created_at: string;
	visit_id: string;
	page_id: string;
	session_id: string;
	page_path: string;
	niche: string;
	viewport_width: number;
	viewport_height: number;
	event_type: string;
	event_props: Record<string, unknown>;
}

/** events/list — listado crudo paginado de eventos. */
export interface EventListResponse {
	items: EventRow[];
	page: number;
	page_size: number;
	total: number;
	has_more: boolean;
}

/** Params del listado paginado de eventos (events/list). */
export interface EventListParams extends DateRangeParams {
	page?: number;
	page_size?: number;
	niche?: string;
	event_type?: string;
	session_id?: string;
	page_path?: string;
}

/** Una celda del heatmap (events/heatmap). */
export interface HeatmapCell {
	dow: number;
	hour: number;
	count: number;
}

/** events/heatmap — distribucion de eventos por dia de semana x hora. */
export interface HeatmapResponse {
	cells: HeatmapCell[];
}
