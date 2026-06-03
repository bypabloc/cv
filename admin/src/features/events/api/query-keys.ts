import { metricsKey } from "@/lib/metrics-query-keys";
import type { DateRangeParams, EventListParams } from "../types";

/**
 * @module features/events/api/query-keys
 * @description Query keys del dominio `events`, derivadas del namespace raiz
 *   `['metrics', 'events', <action>, params]`.
 */
export const eventsKeys = {
	distribution: (params: DateRangeParams) =>
		metricsKey("events", "distribution", params),
	list: (params: EventListParams) => metricsKey("events", "list", params),
	heatmap: (params: DateRangeParams) => metricsKey("events", "heatmap", params),
};
