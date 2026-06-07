"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { adminKeys } from "../api/query-keys";
import { usersAdminClient } from "../api/users-admin-client";

/**
 * @function useEnableUser
 * @description Rehabilita un usuario (admin.enable-user). En exito invalida
 *   `adminKeys.users` + `adminKeys.user(user_id)` + `adminKeys.actions` y
 *   muestra un toast de exito; en error muestra el mensaje.
 */
export function useEnableUser() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: usersAdminClient.enableUser,
		onSuccess: (_data, variables) => {
			void queryClient.invalidateQueries({ queryKey: adminKeys.usersAll() });
			void queryClient.invalidateQueries({
				queryKey: adminKeys.user(variables.user_id),
			});
			void queryClient.invalidateQueries({ queryKey: adminKeys.actions() });
			toast.success("Usuario habilitado");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
