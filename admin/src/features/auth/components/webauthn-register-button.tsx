"use client";

import { startRegistration, WebAuthnError } from "@simplewebauthn/browser";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api-client";
import { useWebauthnRegisterOptions } from "../hooks/use-webauthn-register-options";
import { useWebauthnRegisterVerify } from "../hooks/use-webauthn-register-verify";

/**
 * @function describeRegisterError
 * @description Traduce el error del flujo a un mensaje accionable. El
 *   `navigator.credentials.create()` (via @simplewebauthn) lanza
 *   `WebAuthnError` con un `code` semantico cuando el ceremony falla ANTES
 *   o DURANTE el dialogo del sistema (ej. el authenticator ya tenia el
 *   passkey -> `InvalidStateError`); el backend lanza `ApiError`. Un toast
 *   generico oculta la causa y hace el bug indiagnosticable.
 *
 * @param {unknown} error - El error capturado en onRegister.
 * @returns {string} Mensaje para el usuario con la causa real.
 */
function describeRegisterError(error: unknown): string {
	if (error instanceof WebAuthnError) {
		if (error.name === "InvalidStateError") {
			return "Este dispositivo ya tiene un passkey registrado para tu cuenta.";
		}
		return `No pudimos crear el passkey: ${error.message}`;
	}
	if (error instanceof ApiError) {
		return `El servidor rechazo el passkey (${error.code}): ${error.message}`;
	}
	return "No pudimos registrar el passkey";
}

/**
 * @component WebAuthnRegisterButton
 * @description Registra un passkey: register-options ->
 *   `startRegistration(options.publicKey)` -> register-verify
 *   (`{challenge_id, response, nickname}`). Requiere sesion activa. El
 *   backend devuelve las options ENVUELTAS en `publicKey`; @simplewebauthn
 *   espera el contenido plano de ese `publicKey` en `optionsJSON`.
 *   El verify se espera con `mutateAsync` DENTRO del try para que un fallo
 *   del backend tambien se capture (no fire-and-forget silencioso).
 */
export function WebAuthnRegisterButton() {
	const [nickname, setNickname] = useState("");
	const registerOptions = useWebauthnRegisterOptions();
	const registerVerify = useWebauthnRegisterVerify();
	const isPending = registerOptions.isPending || registerVerify.isPending;

	const onRegister = async () => {
		try {
			const { data } = await registerOptions.mutateAsync();
			const response = await startRegistration({
				optionsJSON: data.options.publicKey,
			});
			await registerVerify.mutateAsync({
				challenge_id: data.challenge_id,
				response,
				nickname: nickname || undefined,
			});
			toast.success("Passkey registrado");
			setNickname("");
		} catch (error) {
			console.error("[webauthn-register]", error);
			toast.error(describeRegisterError(error));
		}
	};

	return (
		<div className="space-y-2">
			<Label htmlFor="passkey-nickname">Nombre del passkey (opcional)</Label>
			<Input
				id="passkey-nickname"
				value={nickname}
				onChange={(event) => setNickname(event.target.value)}
				placeholder="Mi YubiKey"
			/>
			<Button
				type="button"
				className="w-full"
				disabled={isPending}
				onClick={() => {
					void onRegister();
				}}
			>
				{isPending ? "Registrando..." : "Agregar passkey"}
			</Button>
		</div>
	);
}
