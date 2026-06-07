"use client";

import { useMutation } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useSessionRefresh
 * @description Refresca la sesion manualmente. Setea access + refresh nuevos
 *   en el store. El parametro `refresh_token` se resuelve del store si el
 *   caller no lo pasa. (El refresh reactivo del 401 lo hace el `api-client`
 *   centralizado; el refresh-en-reload lo hace `useSessionRehydrate`.)
 */
export function useSessionRefresh() {
	const setAccessToken = useAuthStore((s) => s.setAccessToken);
	const setRefreshToken = useAuthStore((s) => s.setRefreshToken);

	return useMutation({
		mutationFn: () => {
			const refreshToken = useAuthStore.getState().refreshToken;
			return authClient.sessionRefresh({ refresh_token: refreshToken ?? "" });
		},
		onSuccess: ({ data }) => {
			setAccessToken(data.access_token);
			setRefreshToken(data.refresh_token);
		},
	});
}
