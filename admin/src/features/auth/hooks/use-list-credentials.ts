"use client";

import { useQuery } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { authKeys } from "../api/query-keys";

/**
 * @function useListCredentials
 * @description Lista los passkeys WebAuthn del usuario. queryKey
 *   `authKeys.webauthn()`. Devuelve el array de credentials desempaquetado.
 */
export function useListCredentials() {
	return useQuery({
		queryKey: authKeys.webauthn(),
		queryFn: async () => {
			const { data } = await authClient.webauthnListCredentials();
			return data.credentials;
		},
	});
}
