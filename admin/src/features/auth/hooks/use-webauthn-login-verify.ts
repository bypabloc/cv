"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ApiError } from "@/lib/api-client";
import { ROUTES } from "@/lib/routes";
import { authClient } from "../api/auth-client";
import { isAuthResponse } from "../lib/verify-result";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useWebauthnLoginVerify
 * @description Cierra el login con passkey. Sin `silent`: si el VerifyResult es
 *   un AuthResponse setTokens + redirect; el 401 (clone detection) NO setea
 *   tokens. Con `silent` (checklist): NO setea tokens ni redirige — el caller
 *   lee el resultado (via `mutateAsync`) y el checklist decide segun
 *   `mfa_complete`. El error 401 igual se silencia para que el caller lo
 *   maneje.
 *
 * @param {object} [opts] - Opciones de control de flujo
 * @param {boolean} [opts.silent] - No setea tokens ni redirige (modo checklist)
 */
export function useWebauthnLoginVerify(opts?: { silent?: boolean }) {
	const router = useRouter();
	const setTokens = useAuthStore((s) => s.setTokens);
	const silent = opts?.silent ?? false;

	return useMutation({
		mutationFn: authClient.webauthnLoginVerify,
		onSuccess: ({ data }) => {
			if (silent) return;
			if (isAuthResponse(data) && data.user) {
				setTokens(data.access_token, data.refresh_token, data.user);
				router.replace(ROUTES.admin.root);
				toast.success("Sesion iniciada");
			}
		},
		onError: (error) => {
			if (silent) return;
			if (error instanceof ApiError && error.status === 401) {
				toast.error("No pudimos validar el passkey");
				return;
			}
			toast.error(error.message);
		},
	});
}
