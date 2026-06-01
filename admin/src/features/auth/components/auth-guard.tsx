"use client";

import type { ReactNode } from "react";
import { useAuthTimer } from "../hooks/use-auth-timer";
import { useMultiTabSync } from "../hooks/use-multi-tab-sync";
import { useProtectedRoute } from "../hooks/use-protected-route";

/**
 * @component AuthGuard
 * @description Protege el area autenticada. Si no hay sesion, redirige a
 *   `/login?next=<path>` y muestra un placeholder. Monta `useAuthTimer`
 *   (auto-refresh + bootstrap) y `useMultiTabSync` (logout multi-tab).
 *
 * @props {ReactNode} children - Arbol protegido
 */
export function AuthGuard({ children }: { children: ReactNode }) {
	useAuthTimer();
	useMultiTabSync();
	const authed = useProtectedRoute();

	if (!authed) {
		return (
			<div className="flex h-screen items-center justify-center">
				<p className="text-muted-foreground">Verificando sesion...</p>
			</div>
		);
	}

	return <>{children}</>;
}
