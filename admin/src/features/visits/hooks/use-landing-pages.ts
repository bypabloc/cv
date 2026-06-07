"use client";

import { useQuery } from "@tanstack/react-query";
import { visitsKeys } from "../api/query-keys";
import { visitsClient } from "../api/visits-client";
import type { LandingPagesParams } from "../types";

/**
 * @function useLandingPages
 * @description Ranking de landing pages por visitas (visits/landing-pages).
 *   staleTime 60s (ranking agregado, matchea el TTL de cache del backend).
 * @param params - rango (from/to) + limit
 */
export function useLandingPages(params: LandingPagesParams) {
	return useQuery({
		queryKey: visitsKeys.landingPages(params),
		queryFn: () => visitsClient.landingPages(params),
		staleTime: 60_000,
	});
}
