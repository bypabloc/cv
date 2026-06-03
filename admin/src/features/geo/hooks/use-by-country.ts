"use client";

import { useQuery } from "@tanstack/react-query";
import { geoClient } from "../api/geo-client";
import { geoKeys } from "../api/query-keys";
import type { GeoByCountryParams } from "../types";

/**
 * @function useByCountry
 * @description Ranking de paises por sesiones (geo/by-country). staleTime 60s
 *   (matchea el TTL de cache del backend para las queries agregadas).
 * @param params - rango de fechas (from/to) + limite de filas
 */
export function useByCountry(params: GeoByCountryParams) {
	return useQuery({
		queryKey: geoKeys.byCountry(params),
		queryFn: () => geoClient.byCountry(params),
		staleTime: 60_000,
	});
}
