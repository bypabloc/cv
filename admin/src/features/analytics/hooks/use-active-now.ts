"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsClient } from "../api/analytics-client";
import { analyticsKeys } from "../api/query-keys";

/**
 * @function useActiveNow
 * @description Contador de sesiones activas (analytics/active-now). SIN polling:
 *   se recarga con el boton "Actualizar" de /metrics. NO depende del rango.
 *
 * @param options - `enabled` desactiva la query (default true). La page
 *   /metrics lo apaga porque ya recibe active-now en el payload del dashboard.
 */
export function useActiveNow({ enabled = true }: { enabled?: boolean } = {}) {
	return useQuery({
		queryKey: analyticsKeys.activeNow(),
		queryFn: () => analyticsClient.activeNow(),
		staleTime: 30_000,
		refetchOnWindowFocus: false,
		enabled,
	});
}
