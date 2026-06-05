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
import { useLoginVerifyCode } from "../hooks/use-login-verify-code";
import { useAuthStore } from "../store/use-auth-store";

const CODE_LENGTH = 8;
const CROCKFORD = /^[0-9A-HJ-NP-Z]*$/;

/**
 * @component VerifyCodeInput
 * @description InputOTP de 8 chars (alfabeto Crockford) para
 *   `login.verify-code`.
 *
 *   Dos modos:
 *   - Checklist (props `tempToken` + `onResult`): usa el `tempToken` recibido
 *     y entrega el VerifyResult al `onResult`; NO setea tokens ni redirige.
 *   - Standalone (sin props): toma el temp_token del store y el hook cierra el
 *     login (usado en /verify).
 *
 * @props {string} [tempToken] - temp JWT del checklist (modo checklist)
 * @props {(data: VerifyResult) => void} [onResult] - resultado del verify
 * @props {string} [testid] - data-testid del input (modo checklist)
 */
export function VerifyCodeInput({
	tempToken: tempTokenProp,
	onResult,
	testid,
}: {
	tempToken?: string;
	onResult?: (data: VerifyResult) => void;
	testid?: string;
} = {}) {
	const checklistMode = tempTokenProp !== undefined && onResult !== undefined;
	const [code, setCode] = useState("");
	const storeTempToken = useAuthStore((s) => s.tempToken);
	const verify = useLoginVerifyCode();

	const checklistVerify = useMutation({
		mutationFn: authClient.loginVerifyCode,
		onSuccess: ({ data }) => {
			onResult?.(data);
		},
	});

	const isPending = checklistMode
		? checklistVerify.isPending
		: verify.isPending;

	const onSubmit = (event: React.FormEvent) => {
		event.preventDefault();
		if (code.length !== CODE_LENGTH) return;
		if (checklistMode) {
			checklistVerify.mutate({ code, temp_token: tempTokenProp });
			return;
		}
		if (!storeTempToken) return;
		verify.mutate({ code, temp_token: storeTempToken });
	};

	const tokenMissing = checklistMode ? false : !storeTempToken;

	return (
		<form onSubmit={onSubmit} className="space-y-4">
			<InputOTP
				maxLength={CODE_LENGTH}
				value={code}
				onChange={(value) => {
					const upper = value.toUpperCase();
					if (CROCKFORD.test(upper)) setCode(upper);
				}}
				aria-label="Codigo de verificacion"
				data-testid={testid}
			>
				<InputOTPGroup>
					{Array.from({ length: CODE_LENGTH }, (_, i) => (
						// biome-ignore lint/suspicious/noArrayIndexKey: el slot OTP es posicional y de longitud fija; el index es su identificador canonico
						<InputOTPSlot key={`otp-login-${i}`} index={i} />
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
		</form>
	);
}
