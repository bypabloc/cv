"use client";

import { useQuery } from "@tanstack/react-query";
import { devicesClient } from "../api/devices-client";
import { devicesKeys } from "../api/query-keys";
import type { BreakdownParams } from "../types";

/**
 * @function useBreakdown
 * @description Distribucion de sesiones por tipo de dispositivo, navegador y
 *   sistema operativo (devices/breakdown). staleTime 60s (agregada, matchea el
 *   TTL de cache del backend).
 * @param range - rango de fechas (from/to)
 */
export function useBreakdown(range: BreakdownParams) {
	return useQuery({
		queryKey: devicesKeys.breakdown(range),
		queryFn: () => devicesClient.breakdown(range),
		staleTime: 60_000,
	});
}
