"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { authClient } from "@/features/auth/api/auth-client";
import { authKeys } from "@/features/auth/api/query-keys";
import { ApiError } from "@/lib/api-client";
import type { MfaKind, SecurityMethodType } from "@/types/models";

/**
 * @typedef SetRequiredVars
 * @description Variables de la mutation. Para metodos MFA (`totp` /
 *   `email_code`) se usa `kind`; para `webauthn` se usa `recordId` (el
 *   `credential_id`). `required` es el estado DESTINO.
 */
export interface SetRequiredVars {
	type: SecurityMethodType;
	kind?: MfaKind;
	recordId?: string;
	required: boolean;
}

/**
 * @function dispatchSetRequired
 * @description Enruta la mutation segun `type`: webauthn via credential_id,
 *   MFA via kind. No aplica a recovery_codes ni password.
 */
async function dispatchSetRequired(vars: SetRequiredVars): Promise<unknown> {
	const { type, kind, recordId, required } = vars;

	if (type === "webauthn") {
		if (!recordId) {
			throw new Error("recordId (credential_id) es obligatorio para webauthn");
		}
		return authClient.webauthnSetRequired({
			credential_id: recordId,
			required,
		});
	}

	if (type === "totp" || type === "email_code") {
		const resolvedKind: MfaKind = kind ?? type;
		return authClient.mfaSetRequired({ kind: resolvedKind, required });
	}

	throw new Error(`No se puede marcar como requerido el metodo: ${type}`);
}

/**
 * @function useSetRequired
 * @description Marca/desmarca un metodo de seguridad como requerido (MFA o
 *   passkey). El 409 NO invalida el overview: muestra el toast y propaga. En
 *   exito invalida `authKeys.securityOverview()`.
 */
export function useSetRequired() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: dispatchSetRequired,
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
