"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { authKeys } from "../api/query-keys";

/**
 * @function useGenerateRecoveryCodes
 * @description Genera 10 recovery codes (mostrados UNA sola vez). El caller
 *   debe forzar al usuario a guardarlos antes de cerrar el modal. En exito
 *   invalida `authKeys.securityOverview()` para que el panel refresque el
 *   conteo total/remaining (de 0 a 10, o el reset tras regenerar).
 */
export function useGenerateRecoveryCodes() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: authClient.mfaRecoveryCodesGenerate,
		onSuccess: () => {
			void queryClient.invalidateQueries({
				queryKey: authKeys.securityOverview(),
			});
		},
	});
}
