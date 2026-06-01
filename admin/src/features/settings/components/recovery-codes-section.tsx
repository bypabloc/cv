"use client";

import { useState } from "react";
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
 * @component RecoveryCodesSection
 * @description Genera 10 recovery codes (mfa.recovery-codes-generate del
 *   feature `auth`) y los muestra UNA sola vez via RecoveryCodesModal.
 *   Regenerar invalida los anteriores.
 */
export function RecoveryCodesSection() {
	const generate = useGenerateRecoveryCodes();
	const [open, setOpen] = useState(false);

	const codes = generate.data?.data.codes ?? [];

	const onGenerate = () => {
		generate.mutate(undefined, {
			onSuccess: () => setOpen(true),
		});
	};

	return (
		<Card>
			<CardHeader>
				<CardTitle>Codigos de recuperacion</CardTitle>
				<CardDescription>
					Usalos para entrar si pierdes tus otros metodos. Generar nuevos
					invalida los anteriores.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Button
					type="button"
					disabled={generate.isPending}
					onClick={onGenerate}
				>
					{generate.isPending ? "Generando..." : "Generar codigos"}
				</Button>
				<RecoveryCodesModal
					open={open}
					codes={codes}
					onClose={() => setOpen(false)}
				/>
			</CardContent>
		</Card>
	);
}
