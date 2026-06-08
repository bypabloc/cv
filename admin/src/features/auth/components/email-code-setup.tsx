"use client";

import type { ReactElement } from "react";
import { Button } from "@/components/ui/button";
import { useSetupEmailCode } from "../hooks/use-setup-email-code";

/**
 * @component EmailCodeSetup
 * @description Setup de email-code (codigo de 8 chars por email). A diferencia
 *   de TOTP NO hay QR ni confirmacion de codigo: el backend lo inserta
 *   confirmado de inmediato (el user ya probo su email al registrarse). Un solo
 *   boton dispara mfa.setup-email-code y queda activo.
 *
 * @props {() => void} [onDone] - callback al activarse (cierra el Dialog padre).
 */
export function EmailCodeSetup({
	onDone,
}: {
	onDone?: () => void;
}): ReactElement {
	const setupEmailCode = useSetupEmailCode();

	const onSubmit = (event: React.FormEvent) => {
		event.preventDefault();
		setupEmailCode.mutate(undefined, {
			onSuccess: () => onDone?.(),
		});
	};

	return (
		<form onSubmit={onSubmit} className="space-y-4">
			<p className="text-sm text-muted-foreground">
				Recibiras un codigo de 8 caracteres en tu email al iniciar sesion. Se
				activa de inmediato, sin escanear nada.
			</p>
			<Button
				type="submit"
				className="w-full"
				disabled={setupEmailCode.isPending}
			>
				{setupEmailCode.isPending ? "Activando..." : "Activar codigo por email"}
			</Button>
		</form>
	);
}
