/**
 * @module features/sessions
 * @description API publica de la feature `sessions` (tracking de visitantes,
 *   operation `sessions` del Lambda `analytics`). Re-exporta el cliente, las
 *   query keys, los hooks, los componentes y los tipos.
 */

export { sessionsKeys } from "./api/query-keys";
export { sessionsClient } from "./api/sessions-client";
export { SessionFilters } from "./components/SessionFilters";
export { SessionsPagination } from "./components/SessionsPagination";
export { SessionsTable } from "./components/SessionsTable";
export { SessionVisitsTable } from "./components/SessionVisitsTable";
export { useSessionDetail } from "./hooks/use-session-detail";
export { useSessionList } from "./hooks/use-session-list";
export type {
	SessionDetailParams,
	SessionDetailResponse,
	SessionListParams,
	SessionListResponse,
	SessionRow,
	VisitRow,
} from "./types";
