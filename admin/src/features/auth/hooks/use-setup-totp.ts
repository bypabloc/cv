"use client";

import { useMutation } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";

/**
 * @function useSetupTotp
 * @description Inicia el setup de TOTP. Devuelve `{secret_b32, otpauth_url}`;
 *   el front renderiza el QR client-side desde `otpauth_url`.
 */
export function useSetupTotp() {
	return useMutation({
		mutationFn: authClient.mfaSetupTotp,
	});
}
