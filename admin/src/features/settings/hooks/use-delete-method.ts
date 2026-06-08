"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { authClient } from "@/features/auth/api/auth-client";
import { authKeys } from "@/features/auth/api/query-keys";
import { ApiError } from "@/lib/api-client";
import type { MfaKind } from "@/types/models";

/**
 * @typedef DeleteMethodVars
 * @description Variables de la mutation. `kind` es el metodo MFA a borrar
 *   (`totp` / `email_code`). El hard-delete deja el metodo en
 *   `configured:false` (vuelve a 'No configurado').
 */
export interface DeleteMethodVars {
	kind: MfaKind;
}

/**
 * @function useDeleteMethod
 * @description Borra (hard-delete) un metodo MFA via `mfa.delete`. A diferencia
 *   de `useToggleMethod` (soft-disable), elimina el row: el metodo desaparece
 *   del overview y un setup posterior empieza de cero. Pensado para el boton
 *   'Eliminar' de un TOTP pendiente (setup abandonado). El 409
 *   (MUST_KEEP_ONE_MFA_METHOD, solo si fuera el ultimo confirmado) muestra el
 *   toast; en exito invalida `authKeys.securityOverview()`.
 */
export function useDeleteMethod() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (vars: DeleteMethodVars) =>
			authClient.mfaDelete({ kind: vars.kind }),
		onSuccess: () => {
			void queryClient.invalidateQueries({
				queryKey: authKeys.securityOverview(),
			});
		},
		onError: (error) => {
			if (error instanceof ApiError && error.status === 409) {
				toast.error("Debes conservar al menos un metodo");
				return;
			}
			toast.error(error.message);
		},
	});
}
