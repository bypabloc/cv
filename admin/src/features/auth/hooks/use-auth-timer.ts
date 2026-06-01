"use client";

import { useEffect, useRef } from "react";
import { env } from "@/lib/env";
import { authClient } from "../api/auth-client";
import { broadcastAuth } from "../lib/broadcast";
import { withRefreshMutex } from "../lib/refresh-mutex";
import { getJwtExpiry } from "../lib/token-expiry";
import { useAuthStore } from "../store/use-auth-store";

const REFRESH_LEAD = env.NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS;

/**
 * @function doRefresh
 * @description Refresca la sesion bajo el mutex (un solo refresh in-flight).
 *   Setea access + refresh nuevos y broadcastea TOKEN_REFRESH; en fallo
 *   resetea el store. Devuelve si tuvo exito.
 */
async function doRefresh(): Promise<boolean> {
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
 * @function useAuthTimer
 * @description Mantiene la sesion viva:
 * - Bootstrap: si hay refresh vigente (`refreshExpiry > now`) pero el access
 *   es null (post-reload), dispara un refresh para hidratar el access.
 * - Programa un setTimeout para refrescar `REFRESH_LEAD` antes del `exp` del
 *   access; refresca de inmediato si ya esta por expirar.
 * - Page Visibility: al volver el foco, refresca si el access esta cerca de
 *   expirar.
 */
export function useAuthTimer(): void {
	const accessToken = useAuthStore((s) => s.accessToken);
	const reset = useAuthStore((s) => s.reset);
	const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

	useEffect(() => {
		if (timerRef.current) clearTimeout(timerRef.current);

		// Bootstrap: hidratar el access desde el refresh tras un reload.
		if (!accessToken) {
			const { refreshToken, refreshExpiry } = useAuthStore.getState();
			if (refreshToken && refreshExpiry && refreshExpiry > Date.now()) {
				void doRefresh().then((ok) => {
					if (!ok) reset();
				});
			}
			return;
		}

		const exp = getJwtExpiry(accessToken);
		if (exp === null) {
			reset();
			return;
		}

		const msUntilRefresh = exp - Date.now() - REFRESH_LEAD;
		if (msUntilRefresh <= 0) {
			void doRefresh().then((ok) => {
				if (!ok) reset();
			});
			return;
		}

		timerRef.current = setTimeout(() => {
			void doRefresh().then((ok) => {
				if (!ok) reset();
			});
		}, msUntilRefresh);

		return () => {
			if (timerRef.current) clearTimeout(timerRef.current);
		};
	}, [accessToken, reset]);

	// Page Visibility: re-check al volver a la tab.
	useEffect(() => {
		function onVisibility(): void {
			if (document.visibilityState !== "visible") return;
			const token = useAuthStore.getState().accessToken;
			if (!token) return;
			const exp = getJwtExpiry(token);
			if (exp === null) {
				useAuthStore.getState().reset();
				return;
			}
			if (Date.now() >= exp - REFRESH_LEAD) {
				void doRefresh().then((ok) => {
					if (!ok) useAuthStore.getState().reset();
				});
			}
		}
		document.addEventListener("visibilitychange", onVisibility);
		return () => document.removeEventListener("visibilitychange", onVisibility);
	}, []);
}
