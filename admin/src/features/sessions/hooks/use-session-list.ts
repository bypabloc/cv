"use client";

import { useQuery } from "@tanstack/react-query";
import { sessionsKeys } from "../api/query-keys";
import { sessionsClient } from "../api/sessions-client";
import type { SessionListParams } from "../types";

/**
 * @function useSessionList
 * @description Listado paginado de sesiones de visitantes (sessions/list).
 *   staleTime 30s (listado crudo). Es PII: la query no se persiste.
 * @param params - rango from/to + page/page_size + filtros device_type/browser
 */
export function useSessionList(params: SessionListParams) {
	return useQuery({
		queryKey: sessionsKeys.list(params),
		queryFn: () => sessionsClient.list(params),
		staleTime: 30_000,
	});
}
