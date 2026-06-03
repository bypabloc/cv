"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useTopNiches
 * @description Ranking de niches por visitas (analytics/top-niches). staleTime 60s.
 * @param range - rango de fechas
 */
export function useTopNiches(range: DateRangeParams) {
	return useQuery({
		queryKey: analyticsKeys.topNiches(range),
		queryFn: () => analyticsClient.topNiches(range),
		staleTime: 60_000,
	});
}
