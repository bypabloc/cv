/**
 * @module features/analytics/types
 * @description Shapes de las respuestas del Lambda `analytics` (operation
 *   `analytics`): overview, timeseries, top-pages, top-referrers, top-niches,
 *   active-now, retention. Espejan el `data` que devuelve cada endpoint.
 */

/** Rango de fechas que comparten todos los endpoints de metricas. */
export interface DateRangeParams {
	from?: string;
	to?: string;
}

/** analytics/overview — 7 KPIs top-level. */
export interface OverviewResponse {
	sessions: number;
	visits: number;
	events: number;
	contacts: number;
	unique_visitors: number;
	avg_visit_duration_sec: number;
	bounce_rate: number;
	from: string;
	to: string;
}

/** Un punto de la serie temporal. */
export interface TimeseriesPoint {
	timestamp: string;
	count: number;
}

/** analytics/timeseries — serie temporal de eventos. */
export interface TimeseriesResponse {
	bucket: string;
	points: TimeseriesPoint[];
	from: string;
	to: string;
	filters: { niche: string | null; event_type: string | null };
}

export interface TimeseriesParams extends DateRangeParams {
	bucket?: "day" | "hour" | "week";
	niche?: string;
	event_type?: string;
}

/** Una pagina rankeada (top-pages). */
export interface TopPageItem {
	page_path: string;
	events: number;
	unique_visitors: number;
	unique_visits: number;
}

export interface TopPagesResponse {
	items: TopPageItem[];
}

export interface TopPagesParams extends DateRangeParams {
	limit?: number;
	niche?: string;
}

/** Un referrer rankeado. */
export interface RankItem {
	referrer?: string;
	utm_source?: string;
	utm_medium?: string;
	utm_campaign?: string;
	visits: number;
	unique_visitors?: number;
}

export interface TopReferrersResponse {
	referrers: RankItem[];
	utm_sources: RankItem[];
	utm_mediums: RankItem[];
	utm_campaigns: RankItem[];
}

/** Un niche rankeado. */
export interface TopNicheItem {
	niche: string;
	visits: number;
	unique_visitors: number;
}

export interface TopNichesResponse {
	items: TopNicheItem[];
}

/** analytics/active-now — contador live de sesiones activas. */
export interface ActiveNowResponse {
	active_sessions: number;
	threshold_minutes: number;
	as_of: string;
}

/** analytics/retention — new vs returning. */
export interface RetentionResponse {
	new_visitors: number;
	returning_visitors: number;
	total: number;
	returning_rate: number;
}
