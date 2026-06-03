"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";
import type { TimeseriesParams } from "../types";

/**
 * @function useTimeseries
 * @description Serie temporal de eventos (analytics/timeseries). staleTime 60s.
 * @param params - rango + bucket (day|hour|week) + filtros opcionales
 */
export function useTimeseries(params: TimeseriesParams) {
	return useQuery({
		queryKey: analyticsKeys.timeseries(params),
		queryFn: () => analyticsClient.timeseries(params),
		staleTime: 60_000,
	});
}
