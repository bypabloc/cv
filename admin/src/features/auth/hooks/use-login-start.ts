"use client";

import { useMutation } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useLoginStart
 * @description Dispara login.start. Recibe `{precheckToken, email?}`: el
 *   `precheckToken` es el temp JWT que devolvio login.check-email; se manda en
 *   `Authorization: Bearer` (login.start ya NO usa Turnstile). `email` solo va
 *   para el alta fusionada (email nuevo); para un user existente el user se
 *   resuelve por el `sub` del precheck y NO se envia. En exito guarda el
 *   temp_token de la respuesta (el caller decide el siguiente paso segun
 *   `methods`).
 */
export function useLoginStart() {
	const setTempToken = useAuthStore((s) => s.setTempToken);

	return useMutation({
		mutationFn: ({
			precheckToken,
			email,
		}: {
			precheckToken: string;
			email?: string;
		}) => authClient.loginStart(precheckToken, email),
		onSuccess: ({ data }) => {
			setTempToken(data.temp_token);
		},
	});
}
