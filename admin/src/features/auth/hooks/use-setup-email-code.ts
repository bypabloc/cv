"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { authKeys } from "../api/query-keys";

/**
 * @function useSetupEmailCode
 * @description Activa MFA via email-code. En exito invalida `authKeys.mfa()`.
 */
export function useSetupEmailCode() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: authClient.mfaSetupEmailCode,
		onSuccess: () => {
			void queryClient.invalidateQueries({ queryKey: authKeys.mfa() });
		},
	});
}
