"use client";

import { useQuery } from "@tanstack/react-query";
import { eventsClient } from "../api/events-client";
import { eventsKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useHeatmap
 * @description Distribucion de eventos por dia de semana x hora
 *   (events/heatmap). staleTime 60s (agregada).
 * @param range - rango de fechas (from/to)
 */
export function useHeatmap(range: DateRangeParams) {
	return useQuery({
		queryKey: eventsKeys.heatmap(range),
		queryFn: () => eventsClient.heatmap(range),
		staleTime: 60_000,
	});
}
