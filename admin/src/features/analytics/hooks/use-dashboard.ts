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
 *   SIN polling: el usuario controla cuando recargar con el boton
 *   "Actualizar" de /metrics (invalida estas queries). staleTime alto para
 *   no re-fetchear en cada navegacion; refetchOnWindowFocus desactivado.
 *
 * @param params - rango (from/to) + bucket de la serie + limit de rankings
 */
export function useDashboard(params: DashboardParams) {
	return useQuery({
		queryKey: analyticsKeys.dashboard(params),
		queryFn: () => analyticsClient.dashboard(params),
		staleTime: 60_000,
		refetchOnWindowFocus: false,
	});
}
