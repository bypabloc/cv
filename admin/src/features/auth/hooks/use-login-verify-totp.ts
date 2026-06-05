"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ROUTES } from "@/lib/routes";
import { authClient } from "../api/auth-client";
import { isAuthResponse } from "../lib/verify-result";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useLoginVerifyTotp
 * @description Verifica el code TOTP (path standalone, store). Si el
 *   VerifyResult es un AuthResponse setea tokens + user y navega al app shell;
 *   si quedan factores (temp_token nuevo, rolling) rota el temp del store. El
 *   400 (codigo invalido) se muestra como toast. El checklist NO usa este hook.
 */
export function useLoginVerifyTotp() {
	const router = useRouter();
	const setTokens = useAuthStore((s) => s.setTokens);
	const setTempToken = useAuthStore((s) => s.setTempToken);

	return useMutation({
		mutationFn: authClient.loginVerifyTotp,
		onSuccess: ({ data }) => {
			if (isAuthResponse(data)) {
				setTokens(data.access_token, data.refresh_token, data.user);
				router.replace(ROUTES.admin.root);
				toast.success("Sesion iniciada");
				return;
			}
			setTempToken(data.temp_token);
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
