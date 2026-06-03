"use client";

import { useEffect } from "react";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useAuthBootstrap
 * @description Gate de hidratacion del store persistido (zustand `persist`).
 *
 * El bug "la sesion no persiste tras reload" es una race: tras un reload el
 * `accessToken` esta solo en memoria (null) y `useProtectedRoute` redirige a
 * /login de forma SINCRONA antes de que `useAuthTimer` hidrate el access desde
 * el refresh token (async). El flag `bootstrapping` (default true) retiene ese
 * redirect; `useAuthTimer` lo apaga cuando el bootstrap resuelve.
 *
 * Este hook cubre el caso DEFENSIVO en que el storage aun no hidrato al primer
 * render (storages async; con localStorage la hidratacion es sincrona y
 * `hasHydrated()` ya es true). Si no hay refresh vigente tras hidratar, apaga
 * `bootstrapping` para permitir el redirect (`useAuthTimer` cubre el caso con
 * refresh vigente disparando el refresh y apagando el flag en su `.then`).
 */
export function useAuthBootstrap(): void {
	useEffect(() => {
		const resolveIfNoRefresh = (): void => {
			const { accessToken, refreshToken, refreshExpiry, setBootstrapping } =
				useAuthStore.getState();
			// Con un refresh vigente, el cierre del flag lo hace `useAuthTimer`
			// (tras el `doRefresh`). Aqui solo cerramos cuando NO hay nada que
			// hidratar (sin refresh, expirado) o ya hay access (sesion en curso).
			const hasLiveRefresh =
				!!refreshToken && !!refreshExpiry && refreshExpiry > Date.now();
			if (accessToken || !hasLiveRefresh) {
				setBootstrapping(false);
			}
		};

		if (useAuthStore.persist.hasHydrated()) {
			resolveIfNoRefresh();
			return;
		}

		// Storage async: esperar a que termine la hidratacion. El unsubscribe
		// del cleanup evita callbacks duplicados (StrictMode monta 2 veces).
		const unsub = useAuthStore.persist.onFinishHydration(resolveIfNoRefresh);
		return unsub;
	}, []);
}
