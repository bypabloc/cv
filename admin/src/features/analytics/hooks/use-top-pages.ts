"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";
import type { TopPagesParams } from "../types";

/**
 * @function useTopPages
 * @description Ranking de paginas mas vistas (analytics/top-pages). staleTime 60s.
 * @param params - rango + limit + niche opcional
 */
export function useTopPages(params: TopPagesParams) {
	return useQuery({
		queryKey: analyticsKeys.topPages(params),
		queryFn: () => analyticsClient.topPages(params),
		staleTime: 60_000,
	});
}
