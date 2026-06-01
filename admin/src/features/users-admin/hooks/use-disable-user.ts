"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { adminKeys } from "../api/query-keys";
import { usersAdminClient } from "../api/users-admin-client";

/**
 * @function useDisableUser
 * @description Deshabilita un usuario (admin.disable-user). En exito invalida
 *   `adminKeys.users` + `adminKeys.user(user_id)` + `adminKeys.actions` y
 *   muestra un toast de exito; en error muestra el mensaje.
 */
export function useDisableUser() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: usersAdminClient.disableUser,
		onSuccess: (_data, variables) => {
			void queryClient.invalidateQueries({ queryKey: adminKeys.usersAll() });
			void queryClient.invalidateQueries({
				queryKey: adminKeys.user(variables.user_id),
			});
			void queryClient.invalidateQueries({ queryKey: adminKeys.actions() });
			toast.success("Usuario deshabilitado");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
