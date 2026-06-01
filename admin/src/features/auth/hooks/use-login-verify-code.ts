"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ROUTES } from "@/lib/routes";
import { authClient } from "../api/auth-client";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useLoginVerifyCode
 * @description Cierra el login con el code de 8 chars. Setea tokens + user y
 *   navega al app shell.
 */
export function useLoginVerifyCode() {
	const router = useRouter();
	const setTokens = useAuthStore((s) => s.setTokens);

	return useMutation({
		mutationFn: authClient.loginVerifyCode,
		onSuccess: ({ data }) => {
			setTokens(data.access_token, data.refresh_token, data.user);
			router.replace(ROUTES.admin.root);
			toast.success("Sesion iniciada");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
