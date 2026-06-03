"use client";

import { useQuery } from "@tanstack/react-query";
import { eventsClient } from "../api/events-client";
import { eventsKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useDistribution
 * @description Ranking de tipos de evento por frecuencia (events/distribution).
 *   staleTime 60s (matchea el TTL de cache del backend para las agregadas).
 * @param range - rango de fechas (from/to)
 */
export function useDistribution(range: DateRangeParams) {
	return useQuery({
		queryKey: eventsKeys.distribution(range),
		queryFn: () => eventsClient.distribution(range),
		staleTime: 60_000,
	});
}
