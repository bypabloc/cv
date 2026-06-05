"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
	InputOTP,
	InputOTPGroup,
	InputOTPSlot,
} from "@/components/ui/input-otp";
import type { VerifyResult } from "@/types/api";
import { authClient } from "../api/auth-client";
import { useLoginVerifyTotp } from "../hooks/use-login-verify-totp";
import { useAuthStore } from "../store/use-auth-store";
import { RecoveryCodeInput } from "./recovery-code-input";

const CODE_LENGTH = 6;
const DIGITS = /^[0-9]*$/;

/**
 * @component LoginTotpInput
 * @description InputOTP de 6 digitos para `login.verify-totp`.
 *
 *   Dos modos:
 *   - Checklist (props `tempToken` + `onResult`): usa el `tempToken` recibido
 *     y entrega el VerifyResult al `onResult`; NO setea tokens ni redirige.
 *   - Standalone (sin props): toma el temp_token del store y el hook cierra el
 *     login. El link "Usar codigo de recuperacion" monta `RecoveryCodeInput`.
 *
 * @props {string} [tempToken] - temp JWT del checklist (modo checklist)
 * @props {(data: VerifyResult) => void} [onResult] - resultado del verify
 * @props {boolean} [withRecovery] - muestra el link de recovery (default true)
 * @props {string} [testid] - data-testid del input (modo checklist)
 */
export function LoginTotpInput({
	tempToken: tempTokenProp,
	onResult,
	withRecovery = true,
	testid,
}: {
	tempToken?: string;
	onResult?: (data: VerifyResult) => void;
	withRecovery?: boolean;
	testid?: string;
} = {}) {
	const checklistMode = tempTokenProp !== undefined && onResult !== undefined;
	const [code, setCode] = useState("");
	const [useRecovery, setUseRecovery] = useState(false);
	const storeTempToken = useAuthStore((s) => s.tempToken);
	const verifyTotp = useLoginVerifyTotp();

	const checklistVerify = useMutation({
		mutationFn: authClient.loginVerifyTotp,
		onSuccess: ({ data }) => {
			onResult?.(data);
		},
	});

	if (useRecovery) {
		return <RecoveryCodeInput />;
	}

	const isPending = checklistMode
		? checklistVerify.isPending
		: verifyTotp.isPending;

	const onSubmit = (event: React.FormEvent) => {
		event.preventDefault();
		if (code.length !== CODE_LENGTH) return;
		if (checklistMode) {
			checklistVerify.mutate({ code, temp_token: tempTokenProp });
			return;
		}
		if (!storeTempToken) return;
		verifyTotp.mutate({ code, temp_token: storeTempToken });
	};

	const tokenMissing = checklistMode ? false : !storeTempToken;

	return (
		<form onSubmit={onSubmit} className="space-y-4">
			<InputOTP
				maxLength={CODE_LENGTH}
				value={code}
				onChange={(value) => {
					if (DIGITS.test(value)) setCode(value);
				}}
				aria-label="Codigo TOTP"
				data-testid={testid}
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
				disabled={isPending || code.length !== CODE_LENGTH || tokenMissing}
			>
				{isPending ? "Verificando..." : "Verificar"}
			</Button>

			{withRecovery && (
				<Button
					type="button"
					variant="link"
					className="w-full"
					onClick={() => setUseRecovery(true)}
				>
					Usar codigo de recuperacion
				</Button>
			)}
		</form>
	);
}
