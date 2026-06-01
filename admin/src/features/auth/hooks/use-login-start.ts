"use client";

import { useMutation } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useLoginStart
 * @description Dispara login.start. En exito guarda el temp_token (el caller
 *   decide el siguiente paso segun `methods`). El 404 EMAIL_NOT_FOUND con
 *   `suggest_register` lo maneja el componente (`error.data`).
 */
export function useLoginStart() {
	const setTempToken = useAuthStore((s) => s.setTempToken);

	return useMutation({
		mutationFn: authClient.loginStart,
		onSuccess: ({ data }) => {
			setTempToken(data.temp_token);
		},
	});
}
