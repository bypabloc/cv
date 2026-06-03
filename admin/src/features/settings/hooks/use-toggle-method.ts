"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { authClient } from "@/features/auth/api/auth-client";
import { authKeys } from "@/features/auth/api/query-keys";
import { ApiError } from "@/lib/api-client";
import type { MfaKind, SecurityMethodType } from "@/types/models";

/**
 * @typedef ToggleMethodVars
 * @description Variables de la mutation. Para metodos MFA (`totp` /
 *   `email_code`) se usa `kind`; para `webauthn` se usa `recordId` (el
 *   `credential_id` del passkey). `enable` es el estado DESTINO.
 */
export interface ToggleMethodVars {
	type: SecurityMethodType;
	kind?: MfaKind;
	recordId?: string;
	enable: boolean;
}

/**
 * @function dispatchToggle
 * @description Enruta la mutation al metodo correcto del authClient segun
 *   `type` y el estado destino `enable`. MFA via kind; webauthn via recordId.
 */
async function dispatchToggle(vars: ToggleMethodVars): Promise<unknown> {
	const { type, kind, recordId, enable } = vars;

	if (type === "webauthn") {
		if (!recordId) {
			throw new Error("recordId (credential_id) es obligatorio para webauthn");
		}
		return enable
			? authClient.webauthnEnable({ credential_id: recordId })
			: authClient.webauthnDisable({ credential_id: recordId });
	}

	if (type === "totp" || type === "email_code") {
		const resolvedKind: MfaKind = kind ?? type;
		return enable
			? authClient.mfaEnable({ kind: resolvedKind })
			: authClient.mfaDisable({ kind: resolvedKind });
	}

	throw new Error(`No se puede activar/desactivar el metodo: ${type}`);
}

/**
 * @function useToggleMethod
 * @description Activa/desactiva un metodo de seguridad (MFA o passkey). El 409
 *   (MUST_KEEP_ONE_MFA_METHOD) NO invalida el overview: muestra el toast y
 *   propaga. En exito invalida `authKeys.securityOverview()`.
 */
export function useToggleMethod() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: dispatchToggle,
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
