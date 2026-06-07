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
 */
export function WebAuthnLoginButton({
	email: emailProp,
	onResult,
	testid,
}: {
	email?: string;
	onResult?: (data: VerifyResult) => void;
	testid?: string;
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
			const result = await loginVerify.mutateAsync({
				challenge_id: data.challenge_id,
				response,
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
