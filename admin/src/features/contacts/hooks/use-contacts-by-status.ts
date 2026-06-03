"use client";

import { useQuery } from "@tanstack/react-query";
import { contactsClient } from "../api/contacts-client";
import { contactsKeys } from "../api/query-keys";
import type { DateRangeParams } from "../types";

/**
 * @function useContactsByStatus
 * @description Desglose de contactos por estado (contacts/by-status).
 *   staleTime 60s (metrica agregada, matchea el TTL de cache del backend).
 * @param range - rango de fechas (from/to)
 */
export function useContactsByStatus(range: DateRangeParams) {
	return useQuery({
		queryKey: contactsKeys.byStatus(range),
		queryFn: () => contactsClient.byStatus(range),
		staleTime: 60_000,
	});
}
