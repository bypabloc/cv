"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useTopReferrers
 * @description Rankings de referrers + UTM (analytics/top-referrers). staleTime 60s.
 * @param range - rango de fechas
 */
export function useTopReferrers(range: DateRangeParams) {
	return useQuery({
		queryKey: analyticsKeys.topReferrers(range),
		queryFn: () => analyticsClient.topReferrers(range),
		staleTime: 60_000,
	});
}
