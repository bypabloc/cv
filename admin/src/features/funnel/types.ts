/**
 * @module features/funnel/types
 * @description Shapes de las respuestas del Lambda `analytics` (operation
 *   `funnel`): conversion. Espejan el `data` que devuelve cada endpoint.
 */

/** Rango de fechas que comparten los endpoints de funnel. */
export interface DateRangeParams {
	from?: string;
	to?: string;
}

/**
 * funnel/conversion — embudo session -> visit -> contact con sus tasas.
 * Los `*_rate` vienen en [0, 1] (proporcion); se formatean a % en la UI.
 */
export interface FunnelConversionResponse {
	sessions: number;
	visits: number;
	contacts: number;
	session_to_visit_rate: number;
	visit_to_contact_rate: number;
	session_to_contact_rate: number;
}
