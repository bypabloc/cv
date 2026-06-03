import { metricsKey } from "@/lib/metrics-query-keys";
import type { BreakdownParams } from "../types";

/**
 * @module features/devices/api/query-keys
 * @description Query keys del dominio `devices`, derivadas del namespace raiz
 *   `['metrics', 'devices', <action>, params]`.
 */
export const devicesKeys = {
	breakdown: (params: BreakdownParams) =>
		metricsKey("devices", "breakdown", params),
};
