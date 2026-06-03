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
	// Suscribirse a accessToken (NO solo a la fn isAuthenticated): asi el
	// componente re-renderiza cuando el bootstrap hidrata el access desde el
	// refresh, y `authed` se recomputa con el token fresco. Sin esto, el
	// re-render lo disparaba solo `bootstrapping` y `authed` podia quedar
	// stale (false) -> redirect erroneo a /login pese a tener access valido.
	// `authed` se DERIVA del accessToken reactivo (NO de la fn estable
	// isAuthenticated()). Esto es clave con el React Compiler: si solo se
	// llamara isAuthenticated() (referencia estable) y se subscribiera
	// accessToken con un `void` descartable, el Compiler trataba accessToken
	// como dead-code y NO re-renderizaba al hidratarse el access -> el store
	// quedaba authed=true pero la UI atascada en "Verificando sesion". Derivar
	// authed de accessToken lo vuelve un input reactivo real del render.
	const accessToken = useAuthStore((s) => s.accessToken);
	const bootstrapping = useAuthStore((s) => s.bootstrapping);
	// Suscribirse tambien a refreshToken/refreshExpiry: si hay un refresh
	// vigente, la sesion es RECUPERABLE (el bootstrap puede hidratar el access)
	// y NO se debe redirigir todavia, aunque `authed` sea false en este render.
	const refreshToken = useAuthStore((s) => s.refreshToken);
	const refreshExpiry = useAuthStore((s) => s.refreshExpiry);
	const authed = !!accessToken && !isJwtExpired(accessToken);
	const recoverable =
		!!refreshToken && !!refreshExpiry && refreshExpiry > Date.now();

	useEffect(() => {
		// Redirigir SOLO cuando: el bootstrap termino, NO hay sesion activa y la
		// sesion NO es recuperable por un refresh vigente. Mientras haya refresh
		// vivo, esperar al bootstrap (exito -> children; fallo -> el store hace
		// reset, `recoverable` pasa a false -> recien ahi redirige).
		if (!bootstrapping && !authed && !recoverable) {
			router.replace(loginWithNext(pathname));
		}
	}, [authed, bootstrapping, recoverable, router, pathname]);

	return authed;
}
