"use client";

import { useQuery } from "@tanstack/react-query";
import { eventsClient } from "../api/events-client";
import { eventsKeys } from "../api/query-keys";
import type { EventListParams } from "../types";

/**
 * @function useEventList
 * @description Listado crudo paginado de eventos (events/list). staleTime 30s
 *   (listado crudo, no agregado).
 * @param params - rango + paginacion + filtros (niche, event_type, ...)
 */
export function useEventList(params: EventListParams) {
	return useQuery({
		queryKey: eventsKeys.list(params),
		queryFn: () => eventsClient.list(params),
		staleTime: 30_000,
	});
}
