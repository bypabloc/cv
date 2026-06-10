"use client";

import { useQuery } from "@tanstack/react-query";
import { cvAdminClient } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { CvCatalogs } from "../types";

/**
 * @function useCatalogs
 * @description Catalogos (niches/skills/techTags) para los selects de los
 *   forms via content.catalogs. Cambian raramente -> staleTime largo.
 */
export function useCatalogs() {
	return useQuery({
		queryKey: cvKeys.catalogs(),
		queryFn: async (): Promise<CvCatalogs> =>
			(await cvAdminClient.catalogs()).data,
		staleTime: 5 * 60_000,
		refetchOnWindowFocus: false,
	});
}
