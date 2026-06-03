/**
 * @module features/visits
 * @description API publica de la feature `visits` (operation `visits` del
 *   Lambda `analytics`): listado paginado de visitas + ranking de landing pages.
 */

export { visitsKeys } from "./api/query-keys";
export { visitsClient } from "./api/visits-client";
export { LandingPagesTable } from "./components/LandingPagesTable";
export { VisitsTable } from "./components/VisitsTable";
export { useLandingPages } from "./hooks/use-landing-pages";
export { useVisitsList } from "./hooks/use-visits-list";
export type {
	LandingPageItem,
	LandingPagesParams,
	LandingPagesResponse,
	VisitRow,
	VisitsListParams,
	VisitsListResponse,
} from "./types";
