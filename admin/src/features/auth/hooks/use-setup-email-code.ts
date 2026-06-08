"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { authKeys } from "../api/query-keys";

/**
 * @function useSetupEmailCode
 * @description Activa MFA via email-code. En exito invalida `authKeys.mfa()` y
 *   `authKeys.securityOverview()` para que el panel de seguridad refresque la
 *   fila de email_code (pasa a configured + enabled).
 */
export function useSetupEmailCode() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: authClient.mfaSetupEmailCode,
		onSuccess: () => {
			void queryClient.invalidateQueries({ queryKey: authKeys.mfa() });
			void queryClient.invalidateQueries({
				queryKey: authKeys.securityOverview(),
			});
		},
	});
}
