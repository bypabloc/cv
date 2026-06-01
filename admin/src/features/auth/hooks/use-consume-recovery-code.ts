"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ApiError } from "@/lib/api-client";
import { ROUTES } from "@/lib/routes";
import { authClient } from "../api/auth-client";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @function useConsumeRecoveryCode
 * @description Consume un recovery code en el login con MFA (temp JWT step=2).
 *   En exito setTokens + redirect. El 403 RECOVERY_REQUIRES_STRONG_FACTOR NO
 *   setea tokens: muestra el error.
 */
export function useConsumeRecoveryCode() {
	const router = useRouter();
	const setTokens = useAuthStore((s) => s.setTokens);

	return useMutation({
		mutationFn: authClient.mfaRecoveryCodesConsume,
		onSuccess: ({ data }) => {
			setTokens(data.access_token, data.refresh_token, data.user);
			router.replace(ROUTES.admin.root);
			toast.success("Sesion iniciada");
		},
		onError: (error) => {
			if (error instanceof ApiError && error.status === 403) {
				toast.error(
					"Necesitas un factor fuerte para usar un codigo de recuperacion",
				);
				return;
			}
			toast.error(error.message);
		},
	});
}
