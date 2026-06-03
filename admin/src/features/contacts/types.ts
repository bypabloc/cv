/**
 * @module features/contacts/types
 * @description Shapes de las respuestas del Lambda `analytics` (operation
 *   `contacts`): list, by-status. Espejan el `data` que devuelve cada
 *   endpoint. Es una feature PII: el `queryKey[1] === 'contacts'` ya la
 *   excluye del persister (ver metrics-query-keys).
 */

import type { DateRangeParams } from "@/features/analytics/types";

export type { DateRangeParams };

/** Estados validos de un contacto en el embudo. */
export type ContactStatus =
	| "new"
	| "contacted"
	| "qualified"
	| "converted"
	| "rejected";

/** Una fila cruda de contacto (contacts/list) — contiene PII. */
export interface ContactRow {
	id: string;
	created_at: string;
	name: string;
	email: string;
	message: string;
	company: string | null;
	role: string | null;
	service_type: string | null;
	budget: string | null;
	timeline: string | null;
	niche: string;
	status: ContactStatus;
	session_id: string | null;
}

/** contacts/list — listado crudo paginado de contactos. */
export interface ContactListResponse {
	items: ContactRow[];
	page: number;
	page_size: number;
	total: number;
	has_more: boolean;
}

/** Params del listado paginado de contactos (contacts/list). */
export interface ContactListParams extends DateRangeParams {
	page?: number;
	page_size?: number;
	offset?: number;
	status?: ContactStatus;
	niche?: string;
}

/** Una fila del desglose por estado (contacts/by-status). */
export interface ContactStatusItem {
	status: string;
	count: number;
	pct: number;
}

/** contacts/by-status — desglose de contactos por estado. */
export interface ContactByStatusResponse {
	items: ContactStatusItem[];
}
