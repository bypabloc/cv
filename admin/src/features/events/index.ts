/**
 * @module features/events
 * @description API publica de la feature de metricas `events` (operation
 *   `events` del Lambda `analytics`): distribution, list, heatmap.
 */

export { eventsClient } from "./api/events-client";
export { eventsKeys } from "./api/query-keys";
export { EventDistributionChart } from "./components/EventDistributionChart";
export { EventDistributionTable } from "./components/EventDistributionTable";
export { EventHeatmap } from "./components/EventHeatmap";
export { EventListTable } from "./components/EventListTable";
export { useDistribution } from "./hooks/use-distribution";
export { useEventList } from "./hooks/use-event-list";
export { useHeatmap } from "./hooks/use-heatmap";
export type {
	DateRangeParams,
	EventDistributionItem,
	EventDistributionResponse,
	EventListParams,
	EventListResponse,
	EventRow,
	HeatmapCell,
	HeatmapResponse,
} from "./types";
