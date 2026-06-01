"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ROUTES } from "@/lib/routes";
import { authClient } from "../api/auth-client";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useRegisterVerifyCode
 * @description Cierra el register con el code de 8 chars. Setea tokens + user
 *   y navega al app shell.
 */
export function useRegisterVerifyCode() {
	const router = useRouter();
	const setTokens = useAuthStore((s) => s.setTokens);

	return useMutation({
		mutationFn: authClient.registerVerifyCode,
		onSuccess: ({ data }) => {
			setTokens(data.access_token, data.refresh_token, data.user);
			router.replace(ROUTES.admin.root);
			toast.success("Cuenta verificada");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
