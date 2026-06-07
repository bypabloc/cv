import { metricsKey } from "@/lib/metrics-query-keys";
import type { LandingPagesParams, VisitsListParams } from "../types";

/**
 * @module features/visits/api/query-keys
 * @description Query keys del dominio `visits`, derivadas del namespace raiz
 *   `['metrics', 'visits', <action>, params]`.
 */
export const visitsKeys = {
	list: (params: VisitsListParams) => metricsKey("visits", "list", params),
	landingPages: (params: LandingPagesParams) =>
		metricsKey("visits", "landing-pages", params),
};
