"use client";

import { useMutation } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";

/**
 * @function useCheckEmail
 * @description Dispara login.check-email (pre-chequeo del email). En exito el
 *   caller lee `data` (`{exists, has_password?, pending?, unavailable?}`) para
 *   decidir el siguiente paso del flujo. NO devuelve la lista de metodos.
 */
export function useCheckEmail() {
	return useMutation({
		mutationFn: authClient.loginCheckEmail,
	});
}
