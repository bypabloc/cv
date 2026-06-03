"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { loginWithNext } from "@/lib/routes";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useProtectedRoute
 * @description Redirige a `/login?next=<path>` si no hay sesion. Devuelve el
 *   booleano de autenticacion para que el caller decida que renderizar.
 *
 *   NO redirige mientras `bootstrapping === true`: tras un reload el access
 *   esta solo en memoria (null) y `useAuthTimer`/`useAuthBootstrap` aun pueden
 *   hidratarlo desde el refresh token. Redirigir ahi (sincrono) le ganaria al
 *   refresh (async) y romperia la persistencia de sesion.
 *
 * @returns {boolean} true si el usuario esta autenticado
 */
export function useProtectedRoute(): boolean {
	const router = useRouter();
	const pathname = usePathname();
	const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
	const bootstrapping = useAuthStore((s) => s.bootstrapping);
	const authed = isAuthenticated();

	useEffect(() => {
		if (!bootstrapping && !authed) {
			router.replace(loginWithNext(pathname));
		}
	}, [authed, bootstrapping, router, pathname]);

	return authed;
}
