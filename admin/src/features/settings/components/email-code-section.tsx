"use client";

import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { useSetupEmailCode } from "@/features/auth";

/**
 * @component EmailCodeSection
 * @description Activa MFA via codigo por email (mfa.setup-email-code del
 *   feature `auth`). Confirmar el PRIMER metodo MFA revoca la familia de
 *   refresh (AC-27); el api-client re-emite el access tras la respuesta.
 */
export function EmailCodeSection() {
	const setupEmailCode = useSetupEmailCode();

	return (
		<Card>
			<CardHeader>
				<CardTitle>Codigo por email</CardTitle>
				<CardDescription>
					Recibe un codigo de un solo uso en tu correo para iniciar sesion.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Button
					type="button"
					disabled={setupEmailCode.isPending}
					onClick={() => setupEmailCode.mutate()}
				>
					{setupEmailCode.isPending
						? "Activando..."
						: "Activar codigo por email"}
				</Button>
			</CardContent>
		</Card>
	);
}
