"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
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
	type LoginPasswordInput as LoginPasswordValues,
	loginPasswordSchema,
} from "@/lib/validation/auth";
import type { TempTokenResponse, VerifyResult } from "@/types/api";
import { authClient } from "../api/auth-client";
import { useLoginVerifyPassword } from "../hooks/use-login-verify-password";
import { useAuthStore } from "../store/use-auth-store";

type Methods = NonNullable<TempTokenResponse["methods"]>;

/**
 * @component LoginPasswordInput
 * @description Input de password (min 12) para `login.verify-password`.
 *
 *   Dos modos:
 *   - Checklist (props `tempToken` + `onResult`): usa el `tempToken` recibido
 *     y entrega el VerifyResult al `onResult`; NO setea tokens ni redirige
 *     (eso lo decide el checklist).
 *   - Standalone (sin props): toma el temp_token del store; sin MFA el hook
 *     cierra el login, con MFA llama `onMfaRequired(methods)`.
 *
 * @props {string} [tempToken] - temp JWT del checklist (modo checklist)
 * @props {(data: VerifyResult) => void} [onResult] - resultado del verify
 * @props {(methods: Methods) => void} [onMfaRequired] - MFA pendiente (standalone)
 * @props {string} [testid] - data-testid del input (default login-password)
 */
export function LoginPasswordInput({
	tempToken: tempTokenProp,
	onResult,
	onMfaRequired,
	testid = "login-password",
}: {
	tempToken?: string;
	onResult?: (data: VerifyResult) => void;
	onMfaRequired?: (methods: Methods) => void;
	testid?: string;
}) {
	const checklistMode = tempTokenProp !== undefined && onResult !== undefined;
	const storeTempToken = useAuthStore((s) => s.tempToken);
	const verifyPassword = useLoginVerifyPassword({ onMfaRequired });

	const checklistVerify = useMutation({
		mutationFn: authClient.loginVerifyPassword,
		onSuccess: ({ data }) => {
			onResult?.(data);
		},
	});

	const form = useForm<LoginPasswordValues>({
		resolver: zodResolver(loginPasswordSchema),
		defaultValues: { password: "" },
	});

	const isPending = checklistMode
		? checklistVerify.isPending
		: verifyPassword.isPending;

	const onSubmit = form.handleSubmit((values) => {
		if (checklistMode) {
			checklistVerify.mutate(
				{ password: values.password, temp_token: tempTokenProp },
				{
					onError: (error) => {
						if (error instanceof ApiError && error.status === 401) {
							form.setError("password", {
								message: "Contrasena incorrecta",
							});
						}
					},
				},
			);
			return;
		}
		if (!storeTempToken) return;
		verifyPassword.mutate({
			password: values.password,
			temp_token: storeTempToken,
		});
	});

	const disabled = checklistMode ? isPending : isPending || !storeTempToken;

	return (
		<Form {...form}>
			<form onSubmit={onSubmit} className="space-y-4" noValidate>
				<FormField
					control={form.control}
					name="password"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Contrasena</FormLabel>
							<FormControl>
								<Input
									type="password"
									autoComplete="current-password"
									data-testid={testid}
									{...field}
								/>
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>

				<Button type="submit" className="w-full" disabled={disabled}>
					{isPending ? "Verificando..." : "Continuar"}
				</Button>
			</form>
		</Form>
	);
}
