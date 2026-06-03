import { fetchMetric } from "@/lib/metrics-client";
import type {
	LandingPagesParams,
	LandingPagesResponse,
	VisitsListParams,
	VisitsListResponse,
} from "../types";

/**
 * @module features/visits/api/visits-client
 * @description Cliente tipado de la operation `visits` del Lambda `analytics`.
 *   Cada fn hace `GET /analytics?operation=visits&action=...` via `fetchMetric`
 *   (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const visitsClient = {
	list: (params: VisitsListParams) =>
		fetchMetric<VisitsListResponse>("visits", "list", { ...params }),

	landingPages: (params: LandingPagesParams) =>
		fetchMetric<LandingPagesResponse>("visits", "landing-pages", { ...params }),
};
