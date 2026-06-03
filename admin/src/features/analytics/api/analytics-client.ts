import { fetchMetric } from "@/lib/metrics-client";
import type {
	ActiveNowResponse,
	DateRangeParams,
	OverviewResponse,
	RetentionResponse,
	TimeseriesParams,
	TimeseriesResponse,
	TopNichesResponse,
	TopPagesParams,
	TopPagesResponse,
	TopReferrersResponse,
} from "../types";

/**
 * @module features/analytics/api/analytics-client
 * @description Cliente tipado de la operation `analytics` del Lambda
 *   `analytics`. Cada fn hace `GET /analytics?operation=analytics&action=...`
 *   via `fetchMetric` (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const analyticsClient = {
	overview: (params: DateRangeParams) =>
		fetchMetric<OverviewResponse>("analytics", "overview", { ...params }),

	timeseries: (params: TimeseriesParams) =>
		fetchMetric<TimeseriesResponse>("analytics", "timeseries", { ...params }),

	topPages: (params: TopPagesParams) =>
		fetchMetric<TopPagesResponse>("analytics", "top-pages", { ...params }),

	topReferrers: (params: DateRangeParams) =>
		fetchMetric<TopReferrersResponse>("analytics", "top-referrers", {
			...params,
		}),

	topNiches: (params: DateRangeParams) =>
		fetchMetric<TopNichesResponse>("analytics", "top-niches", { ...params }),

	activeNow: () => fetchMetric<ActiveNowResponse>("analytics", "active-now"),

	retention: (params: DateRangeParams) =>
		fetchMetric<RetentionResponse>("analytics", "retention", { ...params }),
};
