"use client";

import { jwtDecode } from "jwt-decode";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { ROUTES } from "@/lib/routes";

/**
 * @page CallbackPage
 * @description Callback del magic-link (ruta `/callback`). El backend redirige
 *   con los tokens en el fragment hash
 *   (`#access=&refresh=&user_id=&email=&refresh_exp=`). Decodea, valida el shape
 *   del JWT, setTokens, limpia el fragment (`history.replaceState`) y navega al
 *   app shell. `useRef` evita doble ejecucion en StrictMode dev.
 */
export default function CallbackPage() {
	const router = useRouter();
	const setTokens = useAuthStore((s) => s.setTokens);
	const ran = useRef(false);

	useEffect(() => {
		if (ran.current) return;
		ran.current = true;

		const fragment = window.location.hash.slice(1);
		if (!fragment) {
			toast.error("Link invalido");
			router.replace(ROUTES.auth.login);
			return;
		}

		const params = new URLSearchParams(fragment);
		const accessToken = params.get("access");
		const refreshToken = params.get("refresh");
		const userId = params.get("user_id");
		const email = params.get("email");
		const refreshExpRaw = params.get("refresh_exp");

		if (!accessToken || !refreshToken || !userId || !email) {
			toast.error("Link incompleto");
			router.replace(ROUTES.auth.login);
			return;
		}

		try {
			// Validar shape del JWT (no la firma — eso lo hace el backend).
			jwtDecode<{ sub: string; exp: number }>(accessToken);
			const refreshExpiry = refreshExpRaw ? Number(refreshExpRaw) : null;
			setTokens(
				accessToken,
				refreshToken,
				{
					id: userId,
					email,
					status: "active",
					has_password: false,
					mfa_methods: [],
				},
				Number.isFinite(refreshExpiry) ? refreshExpiry : null,
			);

			// Limpiar el fragment ANTES de navegar para que el token no quede en
			// window.location.hash ni en el history.
			window.history.replaceState(null, "", ROUTES.home);
			router.replace(ROUTES.admin.root);
			toast.success("Sesion iniciada");
		} catch {
			toast.error("Token invalido");
			router.replace(ROUTES.auth.login);
		}
	}, [router, setTokens]);

	return (
		<div className="flex h-screen items-center justify-center">
			<p className="text-muted-foreground">Iniciando sesion...</p>
		</div>
	);
}
