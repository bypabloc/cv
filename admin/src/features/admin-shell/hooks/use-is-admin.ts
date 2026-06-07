"use client";

import { useQuery } from "@tanstack/react-query";
import { usersAdminClient } from "@/features/users-admin/api/users-admin-client";
import { ApiError } from "@/lib/api-client";

/**
 * @module features/admin-shell/hooks/use-is-admin
 * @description Determina si el usuario autenticado es admin sondeando UNA vez
 *   `users.admin.list-users` (con `page_size: 1`, payload minimo). El backend
 *   responde `200` si el email esta en la whitelist SSM, o `404 NOT_FOUND`
 *   (anti-enumeration) si no. El sidebar usa esto para ocultar los items
 *   `adminOnly` a quien no es admin (en vez de mostrarlos y dejar que la page
 *   reciba el 404). El rol no cambia dentro de la sesion -> staleTime largo.
 */

const ADMIN_PROBE_KEY = ["admin-shell", "is-admin"] as const;

/**
 * @function useIsAdmin
 * @description Sonda el rol admin. La query SIEMPRE resuelve a un booleano: un
 *   `404 NOT_FOUND` (no-admin) se traduce a `false` (NO se propaga como error),
 *   cualquier OTRO error si se propaga (la query queda en `isError`). Mientras
 *   `isPending` el rol no esta resuelto: el caller trata "aun no se sabe" como
 *   "no admin todavia" para no mostrar items que luego se ocultarian.
 *
 * @returns `{ isAdmin: boolean, isResolved: boolean }`
 */
export function useIsAdmin(): { isAdmin: boolean; isResolved: boolean } {
	const query = useQuery({
		queryKey: ADMIN_PROBE_KEY,
		queryFn: async (): Promise<boolean> => {
			try {
				await usersAdminClient.listUsers({ page_size: 1 });
				return true;
			} catch (error) {
				// 404 NOT_FOUND = no-admin (anti-enumeration): no es un fallo, es
				// la respuesta. Cualquier otro error si se propaga.
				if (error instanceof ApiError && error.status === 404) {
					return false;
				}
				throw error;
			}
		},
		staleTime: 5 * 60_000,
		gcTime: 10 * 60_000,
		retry: false,
		refetchOnWindowFocus: false,
	});

	return {
		isAdmin: query.data === true,
		isResolved: query.isSuccess,
	};
}
