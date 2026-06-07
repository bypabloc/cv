"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { authKeys } from "../api/query-keys";

/**
 * @function useWebauthnRegisterVerify
 * @description Cierra el registro de un passkey. El PRIMER metodo MFA revoca la
 *   familia (AC-27). En exito invalida `authKeys.webauthn()` + `authKeys.mfa()`.
 */
export function useWebauthnRegisterVerify() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: authClient.webauthnRegisterVerify,
		onSuccess: () => {
			void queryClient.invalidateQueries({ queryKey: authKeys.webauthn() });
			void queryClient.invalidateQueries({ queryKey: authKeys.mfa() });
		},
	});
}
