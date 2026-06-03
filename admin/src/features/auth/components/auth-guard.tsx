"use client";

import type { ReactNode } from "react";
import { useAuthBootstrap } from "../hooks/use-auth-bootstrap";
import { useAuthTimer } from "../hooks/use-auth-timer";
import { useMultiTabSync } from "../hooks/use-multi-tab-sync";
import { useProtectedRoute } from "../hooks/use-protected-route";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @component AuthGuard
 * @description Protege el area autenticada. Si no hay sesion, redirige a
 *   `/login?next=<path>` y muestra un placeholder. Monta `useAuthBootstrap`
 *   (gate de hidratacion), `useAuthTimer` (auto-refresh + bootstrap) y
 *   `useMultiTabSync` (logout multi-tab).
 *
 *   Muestra "Verificando sesion..." mientras `bootstrapping` (tras un reload,
 *   el access se hidrata desde el refresh antes de decidir el redirect) o
 *   mientras no haya sesion (la redireccion la dispara `useProtectedRoute`).
 *
 * @props {ReactNode} children - Arbol protegido
 */
export function AuthGuard({ children }: { children: ReactNode }) {
	useAuthBootstrap();
	useAuthTimer();
	useMultiTabSync();
	const authed = useProtectedRoute();
	const bootstrapping = useAuthStore((s) => s.bootstrapping);

	if (bootstrapping || !authed) {
		return (
			<div className="flex h-screen items-center justify-center">
				<p className="text-muted-foreground">Verificando sesion...</p>
			</div>
		);
	}

	return <>{children}</>;
}
