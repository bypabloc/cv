"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { ErrorAlert } from "@/components/ui/error-alert";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import {
	TotpSetup,
	useDisableMfa,
	useMfaList,
	useSetPreferredMfa,
} from "@/features/auth";
import type { MfaKind } from "@/types/models";

const KIND_LABEL: Record<MfaKind, string> = {
	totp: "Aplicacion de autenticacion (TOTP)",
	email_code: "Codigo por email",
};

/**
 * @component MfaMethodsList
 * @description Compone los hooks/componentes MFA del feature `auth`: lista los
 *   metodos (useMfaList), permite agregar TOTP (TotpSetup en Dialog), marcar
 *   preferido (useSetPreferredMfa) y desactivar (useDisableMfa). El boton
 *   Disable se deshabilita cuando `total_mfa === 1` (defensa en profundidad;
 *   el backend es la fuente de verdad y responde 409 MUST_KEEP_ONE).
 */
export function MfaMethodsList() {
	const mfaList = useMfaList();
	const setPreferred = useSetPreferredMfa();
	const disableMfa = useDisableMfa();
	const [totpOpen, setTotpOpen] = useState(false);

	if (mfaList.isLoading) {
		return <LoadingSpinner />;
	}

	if (mfaList.isError || !mfaList.data) {
		return (
			<ErrorAlert error={mfaList.error} onRetry={() => mfaList.refetch()} />
		);
	}

	const { methods, total_mfa } = mfaList.data;
	const isLastMethod = total_mfa === 1;
	const hasTotp = methods.some((m) => m.kind === "totp");

	return (
		<Card>
			<CardHeader>
				<CardTitle>Metodos MFA</CardTitle>
				<CardDescription>
					Mantienes al menos un metodo activo para proteger tu cuenta.
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				{methods.length === 0 ? (
					<p className="text-sm text-muted-foreground">
						No tienes metodos MFA configurados.
					</p>
				) : (
					<ul className="space-y-3">
						{methods.map((method) => (
							<li
								key={method.kind}
								className="flex items-center justify-between gap-3 rounded-md border p-3"
							>
								<div className="flex items-center gap-2">
									<span className="text-sm font-medium">
										{KIND_LABEL[method.kind]}
									</span>
									{method.is_preferred ? (
										<Badge variant="secondary">Preferido</Badge>
									) : null}
								</div>
								<div className="flex gap-2">
									{method.is_preferred ? null : (
										<Button
											type="button"
											variant="outline"
											size="sm"
											disabled={setPreferred.isPending}
											onClick={() => setPreferred.mutate({ kind: method.kind })}
										>
											Marcar preferido
										</Button>
									)}
									<Button
										type="button"
										variant="destructive"
										size="sm"
										disabled={isLastMethod || disableMfa.isPending}
										onClick={() => {
											disableMfa.mutate(
												{ kind: method.kind },
												{
													onError: () => {
														// El 409 ya lo muestra useDisableMfa; aqui solo
														// garantizamos que el estado no se desincronice.
														toast.dismiss();
													},
												},
											);
										}}
									>
										Desactivar
									</Button>
								</div>
							</li>
						))}
					</ul>
				)}

				{isLastMethod ? (
					<p className="text-sm text-muted-foreground">
						Debes conservar al menos un metodo MFA activo.
					</p>
				) : null}

				{hasTotp ? null : (
					<Button type="button" onClick={() => setTotpOpen(true)}>
						Agregar aplicacion (TOTP)
					</Button>
				)}

				<Dialog open={totpOpen} onOpenChange={setTotpOpen}>
					<DialogContent>
						<DialogHeader>
							<DialogTitle>Configurar TOTP</DialogTitle>
							<DialogDescription>
								Escanea el QR con tu app de autenticacion y confirma el codigo.
							</DialogDescription>
						</DialogHeader>
						<TotpSetup />
					</DialogContent>
				</Dialog>
			</CardContent>
		</Card>
	);
}
