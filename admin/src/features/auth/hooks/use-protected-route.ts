"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { loginWithNext } from "@/lib/routes";
import { isJwtExpired } from "../lib/token-expiry";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useProtectedRoute
 * @description Redirige a `/login?next=<path>` si no hay sesion. Devuelve el
 *   booleano de autenticacion para que el caller decida que renderizar.
 *
 *   Lazy auth: `authed` se DERIVA del `accessToken` reactivo (NO de una fn
 *   estable) para que el componente re-renderice cuando el refresh-en-reload
 *   hidrata el access. NO redirige mientras `rehydrating === true`: ese refresh
 *   inicial (async) aun puede hidratar el access desde el `refresh_token`, y un
 *   redirect sincrono le ganaria, rompiendo la persistencia de sesion.
 *
 * @param {boolean} rehydrating - true mientras el refresh-en-reload esta en
 *   vuelo (lo provee `useSessionRehydrate`).
 * @returns {boolean} true si el usuario esta autenticado
 */
export function useProtectedRoute(rehydrating: boolean): boolean {
	const router = useRouter();
	const pathname = usePathname();
	const accessToken = useAuthStore((s) => s.accessToken);
	const authed = !!accessToken && !isJwtExpired(accessToken);

	useEffect(() => {
		// Redirigir SOLO cuando el refresh-en-reload ya resolvio y NO hay sesion.
		// Mientras `rehydrating`, esperar (exito -> children; fallo -> el store
		// hace reset y `authed` queda false -> recien ahi redirige).
		if (!rehydrating && !authed) {
			router.replace(loginWithNext(pathname));
		}
	}, [authed, rehydrating, router, pathname]);

	return authed;
}
