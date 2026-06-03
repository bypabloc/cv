import { apiFetch } from "@/lib/api-client";
import type { Envelope } from "@/types/api";

/**
 * @module lib/metrics-client
 * @description Helper GET compartido por todas las features de metricas que
 *   consumen el Lambda `analytics` (`GET /analytics?operation=...&action=...`).
 *
 *   A diferencia del resto del admin (POST `/auth` y `/users` con body
 *   `{operation, action, data}`), el Lambda `analytics` es GET con query
 *   params: `operation` y `action` van en el query string, igual que el
 *   resto del payload. El access JWT viaja en el header `Authorization`
 *   (lo agrega `apiFetch`), NUNCA en query params.
 *
 *   El backend responde FLAT; `apiFetch` lo re-envuelve en
 *   `Envelope<T> = {is_valid, code, data}`. Aqui se devuelve el `data`.
 */

/** Valores admitidos en el query string de un GET de metricas. */
export type MetricParam = string | number | boolean | null | undefined;

/**
 * @function fetchMetric
 * @description Hace `GET /analytics` con `operation`/`action` + params como
 *   query string, adjunta el Bearer (via apiFetch) y devuelve el `data` del
 *   Envelope tipado. Omite los params `null`/`undefined`/`""`.
 *
 * @param operation - dominio de metricas (`analytics`, `events`, ...)
 * @param action - accion (`overview`, `list`, `by-country`, ...)
 * @param params - resto de los query params (from, to, page, filtros, ...)
 * @returns el `data` de la respuesta, tipado como `T`
 */
export async function fetchMetric<T>(
	operation: string,
	action: string,
	params: Record<string, MetricParam> = {},
): Promise<T> {
	const search = new URLSearchParams();
	search.set("operation", operation);
	search.set("action", action);
	for (const [key, value] of Object.entries(params)) {
		if (value === null || value === undefined || value === "") continue;
		search.set(key, String(value));
	}
	const envelope = await apiFetch<Envelope<T>>(
		`/analytics?${search.toString()}`,
		{ method: "GET" },
	);
	return envelope.data;
}
