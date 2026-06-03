import { metricsKey } from "@/lib/metrics-query-keys";
import type {
	DashboardParams,
	DateRangeParams,
	TimeseriesParams,
	TopPagesParams,
} from "../types";

/**
 * @module features/analytics/api/query-keys
 * @description Query keys del dominio `analytics`, derivadas del namespace raiz
 *   `['metrics', 'analytics', <action>, params]`.
 */
export const analyticsKeys = {
	overview: (params: DateRangeParams) =>
		metricsKey("analytics", "overview", params),
	timeseries: (params: TimeseriesParams) =>
		metricsKey("analytics", "timeseries", params),
	topPages: (params: TopPagesParams) =>
		metricsKey("analytics", "top-pages", params),
	topReferrers: (params: DateRangeParams) =>
		metricsKey("analytics", "top-referrers", params),
	topNiches: (params: DateRangeParams) =>
		metricsKey("analytics", "top-niches", params),
	activeNow: () => metricsKey("analytics", "active-now"),
	retention: (params: DateRangeParams) =>
		metricsKey("analytics", "retention", params),
	dashboard: (params: DashboardParams) =>
		metricsKey("analytics", "dashboard", params),
};
