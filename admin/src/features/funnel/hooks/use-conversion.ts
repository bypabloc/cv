"use client";

import { useQuery } from "@tanstack/react-query";
import { funnelClient } from "../api/funnel-client";
import { funnelKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useConversion
 * @description Embudo de conversion (funnel/conversion): session -> visit ->
 *   contact con sus tasas. staleTime 60s (matchea el TTL de cache del backend
 *   para las queries agregadas).
 * @param range - rango de fechas (from/to)
 */
export function useConversion(range: DateRangeParams) {
	return useQuery({
		queryKey: funnelKeys.conversion(range),
		queryFn: () => funnelClient.conversion(range),
		staleTime: 60_000,
	});
}
