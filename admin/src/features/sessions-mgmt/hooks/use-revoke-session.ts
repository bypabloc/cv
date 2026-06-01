"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ApiError } from "@/lib/api-client";
import { sessionsKeys } from "../api/query-keys";
import { sessionsMgmtClient } from "../api/sessions-mgmt-client";

/**
 * @function useRevokeSession
 * @description Revoca una sesion de la cuenta (users.status.revoke-session). El
 *   400 (CANNOT_REVOKE_CURRENT_SESSION) NO invalida la lista: muestra el error
 *   y lo propaga (la sesion actual se cierra con logout, no con revoke). En
 *   exito invalida `sessionsKeys.sessions()`.
 */
export function useRevokeSession() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: sessionsMgmtClient.revokeSession,
		onSuccess: () => {
			void queryClient.invalidateQueries({ queryKey: sessionsKeys.sessions() });
		},
		onError: (error) => {
			if (error instanceof ApiError && error.status === 400) {
				toast.error("No puedes revocar la sesion actual; usa cerrar sesion");
				return;
			}
			toast.error(error.message);
		},
	});
}
