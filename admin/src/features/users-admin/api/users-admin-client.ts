import { apiFetch } from "@/lib/api-client";
import type {
	AdminActionsResponse,
	Envelope,
	ListUsersResponse,
} from "@/types/api";
import type { AdminUser } from "@/types/models";
import type { ListUsersPayload, UserIdPayload } from "../types";

/**
 * @module features/users-admin/api/users-admin-client
 * @description Cliente tipado del Lambda `users` (operation `admin`, solo
 *   admin via whitelist SSM). Todas las actions hacen `POST /users` con body
 *   JSON `{operation: 'admin', action, data}` y respuesta envuelta en
 *   `{is_valid, code, data}`. Un user NO admin recibe `404 NOT_FOUND` en
 *   CUALQUIER action (anti-enumeration). El access JWT lo agrega `apiFetch`.
 */
export const usersAdminClient = {
	/** admin.list-users: 404 NOT_FOUND si el caller no es admin. */
	listUsers: (data: ListUsersPayload = {}) =>
		apiFetch<Envelope<ListUsersResponse>>("/users", {
			method: "POST",
			body: { operation: "admin", action: "list-users", data },
		}),

	/** admin.get-user: 404 NOT_FOUND si no existe o el caller no es admin. */
	getUser: (data: UserIdPayload) =>
		apiFetch<Envelope<{ user: AdminUser }>>("/users", {
			method: "POST",
			body: { operation: "admin", action: "get-user", data },
		}),

	/** admin.disable-user: deshabilita la cuenta del user objetivo. */
	disableUser: (data: UserIdPayload) =>
		apiFetch<Envelope<{ ok: true }>>("/users", {
			method: "POST",
			body: { operation: "admin", action: "disable-user", data },
		}),

	/** admin.enable-user: rehabilita la cuenta del user objetivo. */
	enableUser: (data: UserIdPayload) =>
		apiFetch<Envelope<{ ok: true }>>("/users", {
			method: "POST",
			body: { operation: "admin", action: "enable-user", data },
		}),

	/** admin.delete-user: soft-delete del user objetivo. */
	deleteUser: (data: UserIdPayload) =>
		apiFetch<Envelope<{ ok: true }>>("/users", {
			method: "POST",
			body: { operation: "admin", action: "delete-user", data },
		}),

	/** admin.force-logout: blacklistea las familias del user objetivo. */
	forceLogout: (data: UserIdPayload) =>
		apiFetch<Envelope<{ ok: true }>>("/users", {
			method: "POST",
			body: { operation: "admin", action: "force-logout", data },
		}),

	/** admin.list-admin-actions: log de acciones administrativas (audit). */
	listAdminActions: () =>
		apiFetch<Envelope<AdminActionsResponse>>("/users", {
			method: "POST",
			body: { operation: "admin", action: "list-admin-actions", data: {} },
		}),
};
