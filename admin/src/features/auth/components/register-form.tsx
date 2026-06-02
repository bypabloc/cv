"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
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
import { type RegisterInput, registerSchema } from "@/lib/validation/auth";
import { useRegisterStart } from "../hooks/use-register-start";
import { TurnstileWidget } from "./turnstile-widget";

/**
 * @component RegisterForm
 * @description Form de registro: email + Turnstile. Dispara register.start; el
 *   hook maneja el 409 (email ya registrado) y la navegacion a `/verify`.
 */
export function RegisterForm() {
	const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
	const registerStart = useRegisterStart();

	const form = useForm<RegisterInput>({
		resolver: zodResolver(registerSchema),
		defaultValues: { email: "" },
	});

	const onSubmit = form.handleSubmit((values) => {
		registerStart.mutate({
			email: values.email,
			cf_turnstile_response: turnstileToken ?? "",
		});
	});

	return (
		<Form {...form}>
			<form onSubmit={onSubmit} className="space-y-4" noValidate>
				<FormField
					control={form.control}
					name="email"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Email</FormLabel>
							<FormControl>
								<Input
									type="email"
									autoComplete="email"
									placeholder="tu@email.com"
									data-testid="register-email"
									{...field}
								/>
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>

				<TurnstileWidget onToken={setTurnstileToken} />

				<Button
					type="submit"
					className="w-full"
					data-testid="register-submit"
					disabled={registerStart.isPending || turnstileToken === null}
				>
					{registerStart.isPending ? "Enviando..." : "Crear cuenta"}
				</Button>
			</form>
		</Form>
	);
}
