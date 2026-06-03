import { fetchMetric } from "@/lib/metrics-client";
import type { GeoByCountryParams, GeoByCountryResponse } from "../types";

/**
 * @module features/geo/api/geo-client
 * @description Cliente tipado de la operation `geo` del Lambda `analytics`.
 *   Cada fn hace `GET /analytics?operation=geo&action=...` via `fetchMetric`
 *   (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const geoClient = {
	byCountry: (params: GeoByCountryParams) =>
		fetchMetric<GeoByCountryResponse>("geo", "by-country", { ...params }),
};
