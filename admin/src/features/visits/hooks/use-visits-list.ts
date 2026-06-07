"use client";

import { useQuery } from "@tanstack/react-query";
import { visitsKeys } from "../api/query-keys";
import { visitsClient } from "../api/visits-client";
import type { VisitsListParams } from "../types";

/**
 * @function useVisitsList
 * @description Listado paginado de visitas (visits/list). staleTime 30s
 *   (listado crudo). El backend requiere `offset = (page - 1) * page_size`:
 *   se deriva aqui a partir de `page`/`page_size` para que la page solo
 *   maneje el numero de pagina.
 * @param params - rango + paginacion (page, page_size) + filtros (niche, country)
 */
export function useVisitsList(params: VisitsListParams) {
	const page = params.page ?? 1;
	const pageSize = params.page_size ?? 20;
	const offset = (page - 1) * pageSize;
	const query: VisitsListParams = {
		...params,
		page,
		page_size: pageSize,
		offset,
	};
	return useQuery({
		queryKey: visitsKeys.list(query),
		queryFn: () => visitsClient.list(query),
		staleTime: 30_000,
	});
}
