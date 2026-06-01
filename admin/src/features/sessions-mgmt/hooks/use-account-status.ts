"use client";

import { useQuery } from "@tanstack/react-query";
import { sessionsKeys } from "../api/query-keys";
import { sessionsMgmtClient } from "../api/sessions-mgmt-client";

/**
 * @function useAccountStatus
 * @description Estado de la cuenta auth (users.status.get). queryKey
 *   `sessionsKeys.status()`, staleTime 30s. Devuelve el `StatusResponse`
 *   desempaquetado (`{user_id, status, current_session_id}`).
 */
export function useAccountStatus() {
	return useQuery({
		queryKey: sessionsKeys.status(),
		queryFn: async () => {
			const { data } = await sessionsMgmtClient.getStatus();
			return data;
		},
		staleTime: 30_000,
	});
}
