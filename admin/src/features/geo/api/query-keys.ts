import { metricsKey } from "@/lib/metrics-query-keys";
import type { GeoByCountryParams } from "../types";

/**
 * @module features/geo/api/query-keys
 * @description Query keys del dominio `geo`, derivadas del namespace raiz
 *   `['metrics', 'geo', <action>, params]`.
 */
export const geoKeys = {
	byCountry: (params: GeoByCountryParams) =>
		metricsKey("geo", "by-country", params),
};
