/**
 * @module features/devices
 * @description API publica de la feature `devices` (UI de metricas de la
 *   operation `devices` del Lambda `analytics`).
 */
export { devicesClient } from "./api/devices-client";
export { devicesKeys } from "./api/query-keys";
export { DeviceBreakdown } from "./components/DeviceBreakdown";
export { DistributionChart } from "./components/DistributionChart";
export { useBreakdown } from "./hooks/use-breakdown";
export type {
	BreakdownParams,
	BreakdownResponse,
	BrowserDist,
	DateRangeParams,
	DeviceTypeDist,
	OsDist,
} from "./types";
