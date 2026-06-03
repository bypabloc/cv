"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";

/**
 * @function useActiveNow
 * @description Contador live de sesiones activas (analytics/active-now).
 *   staleTime 10s + refetchInterval 15s (live; TTL backend 10s). NO depende
 *   del rango de fechas.
 */
export function useActiveNow() {
	return useQuery({
		queryKey: analyticsKeys.activeNow(),
		queryFn: () => analyticsClient.activeNow(),
		staleTime: 10_000,
		refetchInterval: 15_000,
	});
}
