import type { DateRangeParams } from "@/features/analytics/types";

/**
 * @module features/geo/types
 * @description Shapes de las respuestas del Lambda `analytics` (operation
 *   `geo`): by-country. Espejan el `data` que devuelve el endpoint.
 */

/** Una fila del ranking por pais (geo/by-country). */
export interface GeoCountryItem {
	/** Codigo ISO-3166-1 alpha-2 del pais, o 'XX' si desconocido. */
	country: string;
	sessions: number;
	visits: number;
	events: number;
}

/** geo/by-country — ranking de paises por sesiones. */
export interface GeoByCountryResponse {
	items: GeoCountryItem[];
	total: number;
}

/** Params de geo/by-country: rango + limite de filas. */
export interface GeoByCountryParams extends DateRangeParams {
	limit?: number;
}
