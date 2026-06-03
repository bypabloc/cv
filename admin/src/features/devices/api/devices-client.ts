import { fetchMetric } from "@/lib/metrics-client";
import type { BreakdownParams, BreakdownResponse } from "../types";

/**
 * @module features/devices/api/devices-client
 * @description Cliente tipado de la operation `devices` del Lambda `analytics`.
 *   Cada fn hace `GET /analytics?operation=devices&action=...` via
 *   `fetchMetric` (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const devicesClient = {
	breakdown: (params: BreakdownParams) =>
		fetchMetric<BreakdownResponse>("devices", "breakdown", { ...params }),
};
