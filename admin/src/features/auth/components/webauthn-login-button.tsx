"use client";

import { startAuthentication } from "@simplewebauthn/browser";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { VerifyResult } from "@/types/api";
import { useWebauthnLoginOptions } from "../hooks/use-webauthn-login-options";
import { useWebauthnLoginVerify } from "../hooks/use-webauthn-login-verify";

/**
 * @component WebAuthnLoginButton
 * @description Login con passkey: pide email -> login-options ->
 *   `startAuthentication(options.publicKey)` -> login-verify
 *   (`{challenge_id, response}`). El backend devuelve las options ENVUELTAS
 *   en `publicKey`; @simplewebauthn espera el contenido plano en `optionsJSON`.
 *
 *   Dos modos:
 *   - Checklist (props `email` + `onResult`): el email ya es conocido (no se
 *     pide), solo muestra el boton; entrega el VerifyResult al `onResult` (NO
 *     setea tokens ni redirige).
 *   - Standalone (sin props): pide el email y el hook cierra el login
 *     passwordless.
 *
 * @props {string} [email] - email conocido (modo checklist)
 * @props {(data: VerifyResult) => void} [onResult] - resultado del verify
 * @props {string} [testid] - data-testid del boton (modo checklist)
 * @props {string} [tempToken] - temp_token rolling del checklist multi-factor;
 *   se manda al login-verify para que el backend acumule los factores ya
 *   satisfechos (ej. password). Sin el, el login multi-factor no converge.
 */
export function WebAuthnLoginButton({
	email: emailProp,
	onResult,
	testid,
	tempToken,
}: {
	email?: string;
	onResult?: (data: VerifyResult) => void;
	testid?: string;
	tempToken?: string;
} = {}) {
	const checklistMode = emailProp !== undefined && onResult !== undefined;
	const [email, setEmail] = useState("");
	const loginOptions = useWebauthnLoginOptions();
	const loginVerify = useWebauthnLoginVerify({ silent: checklistMode });
	const isPending = loginOptions.isPending || loginVerify.isPending;

	const runPasskey = async (targetEmail: string) => {
		const { data } = await loginOptions.mutateAsync({ email: targetEmail });
		const response = await startAuthentication({
			optionsJSON: data.options.publicKey,
		});
		if (checklistMode) {
			// tempToken: en el checklist multi-factor el backend lo necesita para
			// acumular los factores ya satisfechos (ej. password). Sin el, el
			// passkey se verifica aislado y el login nunca converge.
			const result = await loginVerify.mutateAsync({
				challenge_id: data.challenge_id,
				response,
				temp_token: tempToken,
			});
			onResult?.(result.data);
			return;
		}
		loginVerify.mutate({ challenge_id: data.challenge_id, response });
	};

	const onUsePasskey = async (targetEmail: string) => {
		if (!targetEmail) {
			toast.error("Ingresa tu email");
			return;
		}
		try {
			await runPasskey(targetEmail);
		} catch {
			toast.error("No pudimos iniciar el login con passkey");
		}
	};

	if (checklistMode) {
		return (
			<Button
				type="button"
				variant="outline"
				className="w-full"
				data-testid={testid}
				disabled={isPending}
				onClick={() => {
					void onUsePasskey(emailProp);
				}}
			>
				{isPending ? "Validando..." : "Usar passkey"}
			</Button>
		);
	}

	return (
		<div className="space-y-2">
			<Label htmlFor="webauthn-email">Email (para passkey)</Label>
			<Input
				id="webauthn-email"
				type="email"
				autoComplete="email"
				value={email}
				onChange={(event) => setEmail(event.target.value)}
			/>
			<Button
				type="button"
				variant="outline"
				className="w-full"
				disabled={isPending}
				onClick={() => {
					void onUsePasskey(email);
				}}
			>
				{isPending ? "Validando..." : "Usar passkey"}
			</Button>
		</div>
	);
}
