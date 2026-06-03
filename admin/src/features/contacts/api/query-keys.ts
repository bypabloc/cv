import { metricsKey } from "@/lib/metrics-query-keys";
import type { ContactListParams, DateRangeParams } from "../types";

/**
 * @module features/contacts/api/query-keys
 * @description Query keys del dominio `contacts`, derivadas del namespace raiz
 *   `['metrics', 'contacts', <action>, params]`. Al ser feature PII, el
 *   prefijo `contacts` la excluye del persister.
 */
export const contactsKeys = {
	list: (params: ContactListParams) => metricsKey("contacts", "list", params),
	byStatus: (params: DateRangeParams) =>
		metricsKey("contacts", "by-status", params),
};
