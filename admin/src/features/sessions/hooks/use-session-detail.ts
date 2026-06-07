"use client";

import { useQuery } from "@tanstack/react-query";
import { sessionsKeys } from "../api/query-keys";
import { sessionsClient } from "../api/sessions-client";
import type { SessionDetailParams } from "../types";

/**
 * @function useSessionDetail
 * @description Detalle de una sesion de visitante (sessions/detail): sesion +
 *   visitas + events_count. staleTime 0 (siempre fresh). Solo dispara cuando
 *   hay un session_id no vacio.
 * @param params - `{session_id}` de la sesion a inspeccionar
 */
export function useSessionDetail(params: SessionDetailParams) {
	return useQuery({
		queryKey: sessionsKeys.detail(params),
		queryFn: () => sessionsClient.detail(params),
		staleTime: 0,
		enabled: Boolean(params.session_id),
	});
}
