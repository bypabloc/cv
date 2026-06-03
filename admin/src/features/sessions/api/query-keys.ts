import { metricsKey } from "@/lib/metrics-query-keys";
import type { SessionDetailParams, SessionListParams } from "../types";

/**
 * @module features/sessions/api/query-keys
 * @description Query keys del dominio `sessions` (tracking de visitantes),
 *   derivadas del namespace raiz `['metrics', 'sessions', <action>, params]`.
 *   `sessions` es PII -> el persister NO persiste estas queries.
 */
export const sessionsKeys = {
	list: (params: SessionListParams) => metricsKey("sessions", "list", params),
	detail: (params: SessionDetailParams) =>
		metricsKey("sessions", "detail", params),
};
