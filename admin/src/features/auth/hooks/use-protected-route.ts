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
 * @returns {boolean} true si el usuario esta autenticado
 */
export function useProtectedRoute(): boolean {
	const router = useRouter();
	const pathname = usePathname();
	const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
	const authed = isAuthenticated();

	useEffect(() => {
		if (!authed) {
			router.replace(loginWithNext(pathname));
		}
	}, [authed, router, pathname]);

	return authed;
}
