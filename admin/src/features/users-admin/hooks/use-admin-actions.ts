"use client";

import { useQuery } from "@tanstack/react-query";
import { adminKeys } from "../api/query-keys";
import { usersAdminClient } from "../api/users-admin-client";

/**
 * @function useAdminActions
 * @description Lista el log de acciones administrativas (admin.list-admin-actions).
 *   queryKey `adminKeys.actions()`, staleTime 30s. Devuelve el array `actions`
 *   desempaquetado.
 */
export function useAdminActions() {
	return useQuery({
		queryKey: adminKeys.actions(),
		queryFn: async () => {
			const { data } = await usersAdminClient.listAdminActions();
			return data.actions;
		},
		staleTime: 30_000,
	});
}
