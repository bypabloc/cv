"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
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
import { ROUTES } from "@/lib/routes";
import { type LoginInput, loginSchema } from "@/lib/validation/auth";
import { useLoginStart } from "../hooks/use-login-start";
import { TurnstileWidget } from "./turnstile-widget";
import { WebAuthnLoginButton } from "./webauthn-login-button";

/**
 * @component LoginForm
 * @description Form de inicio de sesion: email + Turnstile. Dispara login.start;
 *   en 404 muestra un Alert con boton "Registrate" (suggest_register), en exito
 *   navega a `/verify?flow=login`. Boton alterno para login con passkey.
 */
export function LoginForm() {
	const router = useRouter();
	const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
	const [suggestRegister, setSuggestRegister] = useState(false);
	const loginStart = useLoginStart();

	const form = useForm<LoginInput>({
		resolver: zodResolver(loginSchema),
		defaultValues: { email: "" },
	});

	const onSubmit = form.handleSubmit((values) => {
		setSuggestRegister(false);
		loginStart.mutate(
			{
				email: values.email,
				cf_turnstile_response: turnstileToken ?? "",
			},
			{
				onSuccess: () => {
					router.push(`${ROUTES.auth.verify}?flow=login`);
				},
				onError: (error) => {
					if (error instanceof ApiError && error.status === 404) {
						const data = error.data as {
							data?: { suggest_register?: boolean };
						};
						if (data?.data?.suggest_register) setSuggestRegister(true);
					}
				},
			},
		);
	});

	return (
		<div className="space-y-4">
			{suggestRegister && (
				<Alert variant="destructive">
					<AlertTitle>Ese email no esta registrado</AlertTitle>
					<AlertDescription>
						<Button
							variant="link"
							className="px-0"
							onClick={() => router.push(ROUTES.auth.register)}
						>
							Registrate
						</Button>
					</AlertDescription>
				</Alert>
			)}

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
						disabled={loginStart.isPending || !turnstileToken}
					>
						{loginStart.isPending ? "Enviando..." : "Iniciar sesion"}
					</Button>
				</form>
			</Form>

			<WebAuthnLoginButton />
		</div>
	);
}
