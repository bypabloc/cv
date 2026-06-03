"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";
import type { DashboardParams } from "../types";

/**
 * @function useDashboard
 * @description Una sola query que trae las 7 vistas del overview de /metrics
 *   (analytics/dashboard): overview, timeseries, top-pages, top-referrers,
 *   top-niches, active-now y retention. Reemplaza las 7 requests previas.
 *
 *   staleTime 10s + refetchInterval 15s para mantener vivo el contador
 *   active-now incluido en el payload. Las 7 sub-vistas estan cacheadas en
 *   el backend (60s las agregadas, 10s active-now), asi que el refetch cada
 *   15s solo dispara una query real a Neon para active-now; el resto sale del
 *   cache DDB del Lambda.
 *
 * @param params - rango (from/to) + bucket de la serie + limit de rankings
 */
export function useDashboard(params: DashboardParams) {
	return useQuery({
		queryKey: analyticsKeys.dashboard(params),
		queryFn: () => analyticsClient.dashboard(params),
		staleTime: 10_000,
		refetchInterval: 15_000,
	});
}
