"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useRetention
 * @description New vs returning visitors (analytics/retention). staleTime 60s.
 * @param range - rango de fechas
 */
export function useRetention(range: DateRangeParams) {
	return useQuery({
		queryKey: analyticsKeys.retention(range),
		queryFn: () => analyticsClient.retention(range),
		staleTime: 60_000,
	});
}
