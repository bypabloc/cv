"use client";

import { useMutation } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useLoginStart
 * @description Dispara login.start. Recibe `{data, precheckToken}`: el
 *   `precheckToken` es el temp JWT que devolvio login.check-email; se manda
 *   en `Authorization: Bearer` (login.start ya NO usa Turnstile). En exito
 *   guarda el temp_token de la respuesta (el caller decide el siguiente paso
 *   segun `methods`).
 */
export function useLoginStart() {
	const setTempToken = useAuthStore((s) => s.setTempToken);

	return useMutation({
		mutationFn: ({
			data,
			precheckToken,
		}: {
			data: { email: string; password?: string; niche?: string };
			precheckToken: string;
		}) => authClient.loginStart(data, precheckToken),
		onSuccess: ({ data }) => {
			setTempToken(data.temp_token);
		},
	});
}
