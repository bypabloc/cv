"use client";

import { useMutation } from "@tanstack/react-query";
import { authClient } from "../api/auth-client";

/**
 * @function useWebauthnRegisterOptions
 * @description Pide las options para registrar un passkey (challenge_id en DDB
 *   TTL 5 min). El caller las pasa a `startRegistration`.
 */
export function useWebauthnRegisterOptions() {
	return useMutation({
		mutationFn: authClient.webauthnRegisterOptions,
	});
}
