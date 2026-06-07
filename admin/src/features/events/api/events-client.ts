import { fetchMetric } from "@/lib/metrics-client";
import type {
	DateRangeParams,
	EventDistributionResponse,
	EventListParams,
	EventListResponse,
	HeatmapResponse,
} from "../types";

/**
 * @module features/events/api/events-client
 * @description Cliente tipado de la operation `events` del Lambda `analytics`.
 *   Cada fn hace `GET /analytics?operation=events&action=...` via `fetchMetric`
 *   (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const eventsClient = {
	distribution: (params: DateRangeParams) =>
		fetchMetric<EventDistributionResponse>("events", "distribution", {
			...params,
		}),

	// El backend de `list` requiere `offset` ademas de page/page_size: se
	// deriva como (page - 1) * page_size.
	list: (params: EventListParams) => {
		const page = params.page ?? 1;
		const pageSize = params.page_size ?? 50;
		return fetchMetric<EventListResponse>("events", "list", {
			...params,
			page,
			page_size: pageSize,
			offset: (page - 1) * pageSize,
		});
	},

	heatmap: (params: DateRangeParams) =>
		fetchMetric<HeatmapResponse>("events", "heatmap", { ...params }),
};
