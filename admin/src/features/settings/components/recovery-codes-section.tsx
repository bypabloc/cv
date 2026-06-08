"use client";

import { useState } from "react";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { RecoveryCodesModal, useGenerateRecoveryCodes } from "@/features/auth";

/**
 * @function RecoveryCodesSection
 * @description Genera 10 recovery codes (mfa.recovery-codes-generate del feature
 *   `auth`) y los muestra UNA sola vez via RecoveryCodesModal.
 *
 *   Dos estados segun `total`:
 *   - Sin generar (total === 0): boton 'Generar codigos' directo.
 *   - Ya generados (total > 0): muestra cuantos quedan disponibles + boton
 *     'Regenerar' que abre un AlertDialog advirtiendo que invalida los N codigos
 *     actuales antes de confirmar.
 *
 * @props {number} total - codigos generados en total (del overview).
 * @props {number} remaining - codigos aun disponibles (no consumidos).
 */
export function RecoveryCodesSection({
	total,
	remaining,
}: {
	total: number;
	remaining: number;
}) {
	const generate = useGenerateRecoveryCodes();
	const [open, setOpen] = useState(false);
	const [warnOpen, setWarnOpen] = useState(false);

	const codes = generate.data?.data.codes ?? [];
	const alreadyGenerated = total > 0;

	const runGenerate = () => {
		generate.mutate(undefined, {
			onSuccess: () => setOpen(true),
		});
	};

	return (
		<Card>
			<CardHeader>
				<CardTitle>Codigos de recuperacion</CardTitle>
				<CardDescription>
					{alreadyGenerated
						? `Ya generaste tus codigos de recuperacion: ${remaining} de ${total} disponibles. Guardalos en un lugar seguro; los usas para entrar si pierdes tus otros metodos.`
						: "Genera 10 codigos para entrar si pierdes tus otros metodos. Se muestran una sola vez."}
				</CardDescription>
			</CardHeader>
			<CardContent>
				{alreadyGenerated ? (
					<Button
						type="button"
						variant="outline"
						disabled={generate.isPending}
						onClick={() => setWarnOpen(true)}
					>
						{generate.isPending ? "Regenerando..." : "Regenerar codigos"}
					</Button>
				) : (
					<Button
						type="button"
						disabled={generate.isPending}
						onClick={runGenerate}
					>
						{generate.isPending ? "Generando..." : "Generar codigos"}
					</Button>
				)}

				<AlertDialog open={warnOpen} onOpenChange={setWarnOpen}>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>
								Regenerar codigos de recuperacion
							</AlertDialogTitle>
							<AlertDialogDescription>
								Esto invalida tus {total} codigos actuales (incluidos los{" "}
								{remaining} que aun no usaste). Recibiras 10 nuevos, mostrados
								una sola vez. ¿Continuar?
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel>Cancelar</AlertDialogCancel>
							<AlertDialogAction
								onClick={() => {
									setWarnOpen(false);
									runGenerate();
								}}
							>
								Regenerar
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>

				<RecoveryCodesModal
					open={open}
					codes={codes}
					onClose={() => setOpen(false)}
				/>
			</CardContent>
		</Card>
	);
}
