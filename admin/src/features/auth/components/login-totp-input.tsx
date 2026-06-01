"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
	InputOTP,
	InputOTPGroup,
	InputOTPSlot,
} from "@/components/ui/input-otp";
import { useLoginVerifyTotp } from "../hooks/use-login-verify-totp";
import { useAuthStore } from "../store/use-auth-store";
import { RecoveryCodeInput } from "./recovery-code-input";

const CODE_LENGTH = 6;
const DIGITS = /^[0-9]*$/;

/**
 * @component LoginTotpInput
 * @description Paso final del login con MFA: InputOTP de 6 digitos para
 *   login.verify-totp (usa el temp_token step=2 del store). El link "Usar
 *   codigo de recuperacion" monta `RecoveryCodeInput`.
 */
export function LoginTotpInput() {
	const [code, setCode] = useState("");
	const [useRecovery, setUseRecovery] = useState(false);
	const tempToken = useAuthStore((s) => s.tempToken);
	const verifyTotp = useLoginVerifyTotp();

	if (useRecovery) {
		return <RecoveryCodeInput />;
	}

	const onSubmit = (event: React.FormEvent) => {
		event.preventDefault();
		if (code.length !== CODE_LENGTH || !tempToken) return;
		verifyTotp.mutate({ code, temp_token: tempToken });
	};

	return (
		<form onSubmit={onSubmit} className="space-y-4">
			<InputOTP
				maxLength={CODE_LENGTH}
				value={code}
				onChange={(value) => {
					if (DIGITS.test(value)) setCode(value);
				}}
				aria-label="Codigo TOTP"
			>
				<InputOTPGroup>
					{Array.from({ length: CODE_LENGTH }, (_, i) => (
						// biome-ignore lint/suspicious/noArrayIndexKey: el slot OTP es posicional y de longitud fija; el index es su identificador canonico
						<InputOTPSlot key={`totp-${i}`} index={i} />
					))}
				</InputOTPGroup>
			</InputOTP>

			<Button
				type="submit"
				className="w-full"
				disabled={
					verifyTotp.isPending || code.length !== CODE_LENGTH || !tempToken
				}
			>
				{verifyTotp.isPending ? "Verificando..." : "Verificar"}
			</Button>

			<Button
				type="button"
				variant="link"
				className="w-full"
				onClick={() => setUseRecovery(true)}
			>
				Usar codigo de recuperacion
			</Button>
		</form>
	);
}
