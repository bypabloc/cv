import { fetchMetric } from "@/lib/metrics-client";
import type {
	ContactByStatusResponse,
	ContactListParams,
	ContactListResponse,
	DateRangeParams,
} from "../types";

/**
 * @module features/contacts/api/contacts-client
 * @description Cliente tipado de la operation `contacts` del Lambda
 *   `analytics`. Cada fn hace `GET /analytics?operation=contacts&action=...`
 *   via `fetchMetric` (adjunta el Bearer + refresh) y devuelve el `data`.
 */
export const contactsClient = {
	// El backend de `list` requiere `offset` ademas de page/page_size: se
	// deriva como (page - 1) * page_size.
	list: (params: ContactListParams) => {
		const page = params.page ?? 1;
		const pageSize = params.page_size ?? 50;
		return fetchMetric<ContactListResponse>("contacts", "list", {
			...params,
			page,
			page_size: pageSize,
			offset: (page - 1) * pageSize,
		});
	},

	byStatus: (params: DateRangeParams) =>
		fetchMetric<ContactByStatusResponse>("contacts", "by-status", {
			...params,
		}),
};
