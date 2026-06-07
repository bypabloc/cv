"use client";

import { useQuery } from "@tanstack/react-query";
import { contactsClient } from "../api/contacts-client";
import { contactsKeys } from "../api/query-keys";
import type { ContactListParams } from "../types";

/**
 * @function useContactList
 * @description Listado crudo paginado de contactos (contacts/list). staleTime
 *   30s (listado crudo, no agregado; PII no persistida). Filtra por status y
 *   niche cuando se proveen.
 * @param params - rango + paginacion + filtros (status, niche)
 */
export function useContactList(params: ContactListParams) {
	return useQuery({
		queryKey: contactsKeys.list(params),
		queryFn: () => contactsClient.list(params),
		staleTime: 30_000,
	});
}
