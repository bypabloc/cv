"use client";

import { Button } from "@/components/ui/button";
import { useResendCode } from "../hooks/use-resend-code";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @component MagicLinkPrompt
 * @description Mensaje estatico que indica revisar el email + boton para
 *   reenviar el email (dispara verify.resend-code con el temp_token del store).
 */
export function MagicLinkPrompt() {
	const tempToken = useAuthStore((s) => s.tempToken);
	const resend = useResendCode();

	return (
		<div className="space-y-4 text-center">
			<p className="text-sm text-muted-foreground">
				Te enviamos un email con un link. Haz click ahi para continuar.
			</p>
			<Button
				variant="outline"
				disabled={resend.isPending || !tempToken}
				onClick={() => {
					if (tempToken) resend.mutate({ temp_token: tempToken });
				}}
			>
				{resend.isPending ? "Reenviando..." : "Reenviar email"}
			</Button>
		</div>
	);
}
