"use client";

import type { ReactNode } from "react";
import { useMultiTabSync } from "../hooks/use-multi-tab-sync";
import { useProtectedRoute } from "../hooks/use-protected-route";
import { useSessionRehydrate } from "../hooks/use-session-rehydrate";

/**
 * @component AuthGuard
 * @description Protege el area autenticada (lazy auth). NO verifica
 *   proactivamente el JWT: cada peticion HTTP descubre su propio 401 en el
 *   `api-client` centralizado. Al montar, `useSessionRehydrate` hace UN refresh
 *   silencioso (post-reload) usando el `refresh_token`; `useProtectedRoute`
 *   redirige a `/login?next=<path>` si no hay sesion una vez resuelto ese
 *   refresh. `useMultiTabSync` sincroniza el logout entre tabs.
 *
 *   Sin "Verificando sesion": mientras el refresh-en-reload esta en vuelo
 *   (`rehydrating`) o no hay sesion, no se renderizan los children (el redirect
 *   lo dispara `useProtectedRoute`).
 *
 * @props {ReactNode} children - Arbol protegido
 */
export function AuthGuard({ children }: { children: ReactNode }) {
	const rehydrating = useSessionRehydrate();
	useMultiTabSync();
	const authed = useProtectedRoute(rehydrating);

	if (rehydrating || !authed) {
		return null;
	}

	return <>{children}</>;
}
