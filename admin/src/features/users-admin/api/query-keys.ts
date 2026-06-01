import type { ListUsersPayload } from "../types";

/**
 * @module features/users-admin/api/query-keys
 * @description Query keys estructurados del dominio admin. Las queries usan la
 *   key completa (`users(params)` con paginacion); las mutations invalidan por
 *   PREFIX (`usersAll()` = `['admin', 'users']`) para alcanzar cualquier pagina
 *   cacheada (Tanstack invalida por coincidencia de prefijo). Patron:
 *   `['admin', 'users', {page, page_size}]`, `['admin', 'user', userId]`,
 *   `['admin', 'actions']`.
 */
export const adminKeys = {
	all: ["admin"] as const,
	/** Prefix de todas las queries de listado (sin params): invalidacion masiva. */
	usersAll: () => [...adminKeys.all, "users"] as const,
	/** Key completa de una pagina del listado. */
	users: (params?: ListUsersPayload) =>
		[...adminKeys.usersAll(), params ?? {}] as const,
	user: (userId: string) => [...adminKeys.all, "user", userId] as const,
	actions: () => [...adminKeys.all, "actions"] as const,
};
