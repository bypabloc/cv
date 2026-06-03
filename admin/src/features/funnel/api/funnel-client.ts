import { fetchMetric } from "@/lib/metrics-client";
import type { DateRangeParams, FunnelConversionResponse } from "../types";

/**
 * @module features/funnel/api/funnel-client
 * @description Cliente tipado de la operation `funnel` del Lambda `analytics`.
 *   Cada fn hace `GET /analytics?operation=funnel&action=...` via `fetchMetric`
 *   (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const funnelClient = {
	conversion: (params: DateRangeParams) =>
		fetchMetric<FunnelConversionResponse>("funnel", "conversion", {
			...params,
		}),
};
