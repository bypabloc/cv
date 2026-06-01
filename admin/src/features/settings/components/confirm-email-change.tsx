"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useConfirmEmailChange } from "../hooks/use-change-email";

/**
 * @component ConfirmEmailChange
 * @description Confirma el cambio de email cuando el user vuelve con
 *   `?token=<...>` (deep-link). Lee el token via `useSearchParams` (debe ir
 *   dentro de un boundary Suspense en la page). Si no hay token, no renderiza
 *   nada. Auto-dispara la confirmacion una sola vez al montar.
 */
export function ConfirmEmailChange() {
	const searchParams = useSearchParams();
	const token = searchParams.get("token");
	const confirmEmail = useConfirmEmailChange();
	const ranRef = useRef(false);

	const { mutate } = confirmEmail;
	useEffect(() => {
		if (ranRef.current || !token) return;
		ranRef.current = true;
		mutate({ token });
	}, [token, mutate]);

	if (!token) return null;

	return (
		<Alert>
			<AlertTitle>Confirmacion de email</AlertTitle>
			<AlertDescription className="flex flex-col gap-2">
				{confirmEmail.isPending ? (
					<span>Confirmando tu nuevo email...</span>
				) : confirmEmail.isSuccess ? (
					<span>Tu email fue actualizado correctamente.</span>
				) : confirmEmail.isError ? (
					<>
						<span>No pudimos confirmar el cambio de email.</span>
						<Button
							type="button"
							variant="outline"
							size="sm"
							className="w-fit"
							onClick={() => confirmEmail.mutate({ token })}
						>
							Reintentar
						</Button>
					</>
				) : null}
			</AlertDescription>
		</Alert>
	);
}
