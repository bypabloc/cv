import { fetchMetric } from "@/lib/metrics-client";
import type {
	SessionDetailParams,
	SessionDetailResponse,
	SessionListParams,
	SessionListResponse,
} from "../types";

/**
 * @module features/sessions/api/sessions-client
 * @description Cliente tipado de la operation `sessions` del Lambda
 *   `analytics`. Cada fn hace `GET /analytics?operation=sessions&action=...`
 *   via `fetchMetric` (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const sessionsClient = {
	list: (params: SessionListParams) =>
		fetchMetric<SessionListResponse>("sessions", "list", { ...params }),

	detail: (params: SessionDetailParams) =>
		fetchMetric<SessionDetailResponse>("sessions", "detail", { ...params }),
};
