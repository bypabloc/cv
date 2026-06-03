"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useOverview
 * @description KPIs top-level (analytics/overview). staleTime 60s (matchea el
 *   TTL de cache del backend para las queries agregadas).
 * @param range - rango de fechas (from/to)
 */
export function useOverview(range: DateRangeParams) {
	return useQuery({
		queryKey: analyticsKeys.overview(range),
		queryFn: () => analyticsClient.overview(range),
		staleTime: 60_000,
	});
}
