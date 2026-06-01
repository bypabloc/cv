"use client";

import { QRCodeSVG } from "qrcode.react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
	InputOTP,
	InputOTPGroup,
	InputOTPSlot,
} from "@/components/ui/input-otp";
import { useConfirmTotp } from "../hooks/use-confirm-totp";
import { useSetupTotp } from "../hooks/use-setup-totp";

const CODE_LENGTH = 6;
const DIGITS = /^[0-9]*$/;

/**
 * @component TotpSetup
 * @description Setup de TOTP. Llama mfa.setup-totp al montar y renderiza el QR
 *   CLIENT-SIDE desde `otpauth_url` (el backend NO devuelve imagen). Muestra
 *   `secret_b32` como fallback manual. InputOTP de 6 digitos -> mfa.confirm-totp.
 */
export function TotpSetup() {
	const [code, setCode] = useState("");
	const setupTotp = useSetupTotp();
	const confirmTotp = useConfirmTotp();
	const startedRef = useRef(false);

	useEffect(() => {
		if (startedRef.current) return;
		startedRef.current = true;
		setupTotp.mutate();
	}, [setupTotp]);

	const setup = setupTotp.data?.data;

	const onSubmit = (event: React.FormEvent) => {
		event.preventDefault();
		if (code.length !== CODE_LENGTH) return;
		confirmTotp.mutate({ code });
	};

	if (!setup) {
		return <p className="text-sm text-muted-foreground">Generando codigo...</p>;
	}

	return (
		<div className="space-y-4">
			<QRCodeSVG value={setup.otpauth_url} size={180} />
			<p className="text-sm text-muted-foreground">
				O ingresa el codigo manualmente:{" "}
				<code className="font-mono">{setup.secret_b32}</code>
			</p>

			<form onSubmit={onSubmit} className="space-y-4">
				<InputOTP
					maxLength={CODE_LENGTH}
					value={code}
					onChange={(value) => {
						if (DIGITS.test(value)) setCode(value);
					}}
					aria-label="Codigo TOTP de confirmacion"
				>
					<InputOTPGroup>
						{Array.from({ length: CODE_LENGTH }, (_, i) => (
							// biome-ignore lint/suspicious/noArrayIndexKey: el slot OTP es posicional y de longitud fija; el index es su identificador canonico
							<InputOTPSlot key={`totp-setup-${i}`} index={i} />
						))}
					</InputOTPGroup>
				</InputOTP>

				<Button
					type="submit"
					className="w-full"
					disabled={confirmTotp.isPending || code.length !== CODE_LENGTH}
				>
					{confirmTotp.isPending ? "Confirmando..." : "Confirmar"}
				</Button>
			</form>
		</div>
	);
}
