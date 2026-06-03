"use client";

import { useQuery } from "@tanstack/react-query";
import { authClient } from "@/features/auth/api/auth-client";
import { authKeys } from "@/features/auth/api/query-keys";

/**
 * @function useSecurityOverview
 * @description Lee el overview consolidado de seguridad (security.overview).
 *   queryKey `authKeys.securityOverview()`. Devuelve el
 *   `SecurityOverviewResponse` desempaquetado (`{methods: SecurityMethod[]}`).
 */
export function useSecurityOverview() {
	return useQuery({
		queryKey: authKeys.securityOverview(),
		queryFn: async () => {
			const { data } = await authClient.securityOverview();
			return data;
		},
	});
}
