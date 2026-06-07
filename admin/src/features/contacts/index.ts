/**
 * @module features/contacts
 * @description API publica de la feature de metricas `contacts` (operation
 *   `contacts` del Lambda `analytics`): list, by-status. Es una feature PII.
 */

export { contactsClient } from "./api/contacts-client";
export { contactsKeys } from "./api/query-keys";
export { ContactByStatusChart } from "./components/ContactByStatusChart";
export { ContactByStatusTable } from "./components/ContactByStatusTable";
export { ContactListTable } from "./components/ContactListTable";
export { ContactStatusBadge } from "./components/ContactStatusBadge";
export { ContactStatusFilter } from "./components/ContactStatusFilter";
export { useContactList } from "./hooks/use-contact-list";
export { useContactsByStatus } from "./hooks/use-contacts-by-status";
export type {
	ContactByStatusResponse,
	ContactListParams,
	ContactListResponse,
	ContactRow,
	ContactStatus,
	ContactStatusItem,
	DateRangeParams,
} from "./types";
