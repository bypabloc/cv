import { metricsKey } from "@/lib/metrics-query-keys";
import type { DateRangeParams } from "../types";

/**
 * @module features/funnel/api/query-keys
 * @description Query keys del dominio `funnel`, derivadas del namespace raiz
 *   `['metrics', 'funnel', <action>, params]`.
 */
export const funnelKeys = {
	conversion: (params: DateRangeParams) =>
		metricsKey("funnel", "conversion", params),
};
