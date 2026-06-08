"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { authClient } from "@/features/auth/api/auth-client";
import { authKeys } from "@/features/auth/api/query-keys";
import { ApiError } from "@/lib/api-client";
import type { SecurityPasskey } from "@/types/models";

/**
 * @typedef SetPasskeysGroupRequiredVars
 * @description Variables del toggle MAESTRO del grupo de passkeys.
 *   `required` es el estado DESTINO del grupo (exigir passkey al loguear o no);
 *   `passkeys` es la lista actual de credenciales del overview.
 */
export interface SetPasskeysGroupRequiredVars {
	required: boolean;
	passkeys: SecurityPasskey[];
}

/**
 * @function planGroupRequired
 * @description Calcula que credential_ids hay que mutar (set-required) para
 *   pasar el GRUPO de passkeys al estado `required` destino, preservando los
 *   toggles individuales:
 *
 *   - destino `true` (exigir): si ninguna passkey activa esta marcada, marca la
 *     PRIMERA passkey activa (basta una al loguear; el factor webauthn se
 *     satisface con cualquiera). Si ya hay >=1 requerida, no toca nada (idempotente).
 *   - destino `false` (no exigir): quita `required` de TODAS las que lo tengan.
 *
 *   Funcion pura para testear el invariante sin red.
 *
 * @returns {{ credential_id: string; required: boolean }[]} mutaciones a aplicar.
 */
export function planGroupRequired(
	required: boolean,
	passkeys: SecurityPasskey[],
): { credential_id: string; required: boolean }[] {
	if (required) {
		const alreadyRequired = passkeys.some((pk) => pk.enabled && pk.required);
		if (alreadyRequired) {
			return [];
		}
		const firstActive = passkeys.find((pk) => pk.enabled);
		return firstActive
			? [{ credential_id: firstActive.credential_id, required: true }]
			: [];
	}
	return passkeys
		.filter((pk) => pk.required)
		.map((pk) => ({ credential_id: pk.credential_id, required: false }));
}

/**
 * @function useSetPasskeysGroupRequired
 * @description Toggle MAESTRO de 'Requerido al loguear' del grupo de passkeys.
 *   Activar exige passkey al iniciar sesion (marca una si ninguna lo estaba);
 *   desactivar deja de exigirla (desmarca todas). Los toggles individuales de
 *   cada passkey siguen funcionando aparte. Aplica las mutaciones a
 *   `webauthn.set-required` en serie y al terminar invalida el overview. El 409
 *   (MUST_KEEP_ONE) muestra el toast.
 */
export function useSetPasskeysGroupRequired() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (vars: SetPasskeysGroupRequiredVars) => {
			const mutations = planGroupRequired(vars.required, vars.passkeys);
			for (const mutation of mutations) {
				await authClient.webauthnSetRequired(mutation);
			}
		},
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
