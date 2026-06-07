"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
	Form,
	FormControl,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api-client";
import {
	type RecoveryCodeInput as RecoveryValues,
	recoveryCodeSchema,
} from "@/lib/validation/auth";
import type { VerifyResult } from "@/types/api";
import { authClient } from "../api/auth-client";
import { useConsumeRecoveryCode } from "../hooks/use-consume-recovery-code";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @component RecoveryCodeInput
 * @description Input de 10 chars (Crockford) para consumir un recovery code
 *   (`mfa.recovery-codes-consume`). Es el fallback anti-lockout: saltea todos
 *   los metodos `required` y cierra el login.
 *
 *   Dos modos:
 *   - Checklist (props `tempToken` + `onResult`): usa el `tempToken` recibido
 *     y entrega el VerifyResult al `onResult`; NO setea tokens ni redirige.
 *   - Standalone (sin props): toma el temp_token del store y el hook cierra el
 *     login. Maneja el 403 RECOVERY_REQUIRES_STRONG_FACTOR.
 *
 * @props {string} [tempToken] - temp JWT del checklist (modo checklist)
 * @props {(data: VerifyResult) => void} [onResult] - resultado del verify
 * @props {string} [testid] - data-testid del input (modo checklist)
 */
export function RecoveryCodeInput({
	tempToken: tempTokenProp,
	onResult,
	testid,
}: {
	tempToken?: string;
	onResult?: (data: VerifyResult) => void;
	testid?: string;
} = {}) {
	const checklistMode = tempTokenProp !== undefined && onResult !== undefined;
	const storeTempToken = useAuthStore((s) => s.tempToken);
	const consume = useConsumeRecoveryCode();

	const checklistConsume = useMutation({
		mutationFn: authClient.mfaRecoveryCodesConsume,
		onSuccess: ({ data }) => {
			onResult?.(data);
		},
		onError: (error) => {
			if (error instanceof ApiError && error.status === 403) {
				toast.error(
					"Necesitas un factor fuerte para usar un codigo de recuperacion",
				);
				return;
			}
			toast.error(error.message);
		},
	});

	const isPending = checklistMode
		? checklistConsume.isPending
		: consume.isPending;

	const form = useForm<RecoveryValues>({
		resolver: zodResolver(recoveryCodeSchema),
		defaultValues: { code: "" },
	});

	const onSubmit = form.handleSubmit((values) => {
		if (checklistMode) {
			checklistConsume.mutate({ code: values.code, temp_token: tempTokenProp });
			return;
		}
		if (!storeTempToken) return;
		consume.mutate({ code: values.code, temp_token: storeTempToken });
	});

	const disabled = checklistMode ? isPending : isPending || !storeTempToken;

	return (
		<Form {...form}>
			<form onSubmit={onSubmit} className="space-y-4" noValidate>
				<FormField
					control={form.control}
					name="code"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Codigo de recuperacion</FormLabel>
							<FormControl>
								<Input
									autoComplete="one-time-code"
									placeholder="10 caracteres"
									data-testid={testid}
									{...field}
									onChange={(event) =>
										field.onChange(event.target.value.toUpperCase())
									}
								/>
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>

				<Button type="submit" className="w-full" disabled={disabled}>
					{isPending ? "Verificando..." : "Usar codigo"}
				</Button>
			</form>
		</Form>
	);
}
