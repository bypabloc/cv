"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { authClient } from "../api/auth-client";

/**
 * @function useLoginSendEmailCode
 * @description Dispara login.send-email-code (envia el code de 8 chars al
 *   email del user). Paso previo del metodo email_code / passwordless del
 *   checklist cuando `sent` es false. El error se muestra como toast.
 */
export function useLoginSendEmailCode() {
	return useMutation({
		mutationFn: authClient.loginSendEmailCode,
		onSuccess: () => {
			toast.success("Te enviamos un codigo");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
