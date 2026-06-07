"use client";

import { useEffect, useState } from "react";
import { authClient } from "../api/auth-client";
import { broadcastAuth } from "../lib/broadcast";
import { withRefreshMutex } from "../lib/refresh-mutex";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function rehydrateOnce
 * @description UN refresh al montar (post-reload). Usa el `refresh_token`
 *   persistido para obtener un access nuevo — NO valida el access actual (que
 *   tras un reload es null en memoria por diseno). Bajo el mutex (un solo
 *   refresh in-flight). Setea access + refresh y broadcastea; en fallo resetea
 *   el store. Devuelve si tuvo exito.
 */
async function rehydrateOnce(): Promise<boolean> {
	return withRefreshMutex(async () => {
		const refreshToken = useAuthStore.getState().refreshToken;
		if (!refreshToken) return false;
		try {
			const { data } = await authClient.sessionRefresh({
				refresh_token: refreshToken,
			});
			useAuthStore.getState().setAccessToken(data.access_token);
			useAuthStore.getState().setRefreshToken(data.refresh_token);
			broadcastAuth({ type: "TOKEN_REFRESH", token: data.access_token });
			return true;
		} catch {
			return false;
		}
	});
}

/**
 * @function useSessionRehydrate
 * @description Lazy auth: rehidrata la sesion UNA vez al montar, sin verificar
 *   proactivamente el JWT. Tras un reload el access vive solo en memoria (null);
 *   si hay un `refresh_token` vigente, se hace UN refresh silencioso para
 *   obtener un access nuevo. Sin timer proactivo, sin Page Visibility, sin
 *   validar el access: cada peticion HTTP descubre su propio 401 en el
 *   `api-client` centralizado (refresh -> retry -> logout). Si el refresh-en-
 *   reload falla, resetea el store (el `useProtectedRoute` redirige a /login).
 *
 *   Devuelve `rehydrating`: true mientras el refresh inicial esta in-flight
 *   (gate efimero, sin UI de "Verificando sesion"); el `AuthGuard` lo usa para
 *   no redirigir antes de que ese refresh resuelva.
 *
 * @returns {boolean} true mientras el refresh-en-reload esta en vuelo
 */
export function useSessionRehydrate(): boolean {
	// Si ya hay access en memoria (login en curso, multi-tab), no rehidrata.
	const hasAccess = useAuthStore((s) => s.accessToken !== null);
	const [rehydrating, setRehydrating] = useState(() => {
		const { accessToken, refreshToken, refreshExpiry } =
			useAuthStore.getState();
		// Solo rehidratamos si NO hay access pero SI un refresh vigente.
		return (
			accessToken === null &&
			!!refreshToken &&
			!!refreshExpiry &&
			refreshExpiry > Date.now()
		);
	});

	useEffect(() => {
		if (!rehydrating) return;
		if (hasAccess) {
			setRehydrating(false);
			return;
		}
		let active = true;
		void rehydrateOnce().then((ok) => {
			if (!active) return;
			if (!ok) useAuthStore.getState().reset();
			setRehydrating(false);
		});
		return () => {
			active = false;
		};
	}, [rehydrating, hasAccess]);

	return rehydrating;
}
