"use client";

import { zodResolver } from "@hookform/resolvers/zod";
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
import {
	type RecoveryCodeInput as RecoveryValues,
	recoveryCodeSchema,
} from "@/lib/validation/auth";
import { useConsumeRecoveryCode } from "../hooks/use-consume-recovery-code";
import { useAuthStore } from "../store/use-auth-store";

/**
 * @component RecoveryCodeInput
 * @description Input de 10 chars (Crockford) para consumir un recovery code en
 *   el login con MFA. Requiere temp JWT step=2 (factor fuerte). El hook maneja
 *   el 403 RECOVERY_REQUIRES_STRONG_FACTOR y la navegacion en exito.
 */
export function RecoveryCodeInput() {
	const tempToken = useAuthStore((s) => s.tempToken);
	const consume = useConsumeRecoveryCode();

	const form = useForm<RecoveryValues>({
		resolver: zodResolver(recoveryCodeSchema),
		defaultValues: { code: "" },
	});

	const onSubmit = form.handleSubmit((values) => {
		if (!tempToken) return;
		consume.mutate({ code: values.code, temp_token: tempToken });
	});

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

				<Button
					type="submit"
					className="w-full"
					disabled={consume.isPending || !tempToken}
				>
					{consume.isPending ? "Verificando..." : "Usar codigo"}
				</Button>
			</form>
		</Form>
	);
}
