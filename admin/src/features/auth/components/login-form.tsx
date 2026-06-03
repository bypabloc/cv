"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
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
import {
	type LoginInput,
	loginSchema,
	passwordSchema,
} from "@/lib/validation/auth";
import { useCheckEmail } from "../hooks/use-check-email";
import { useLoginStart } from "../hooks/use-login-start";
import { useAuthStore } from "../store/use-auth-store";
import { TurnstileWidget } from "./turnstile-widget";
import { WebAuthnLoginButton } from "./webauthn-login-button";

const passwordStepSchema = z.object({ password: passwordSchema });
type PasswordStepValues = z.infer<typeof passwordStepSchema>;

/** Estado de la maquina del flujo de login (paso 2 segun check-email). */
type Stage =
	| { kind: "email" }
	| { kind: "password"; email: string }
	| { kind: "passwordless"; email: string }
	| { kind: "create"; email: string }
	| { kind: "unavailable" };

/**
 * @component LoginForm
 * @description Login de 2 pasos. Paso 1: email + Turnstile -> login.check-email.
 *   Paso 2 segun el resultado:
 *   - existe + tiene password -> input de password -> login.start con password.
 *   - existe sin password (o pending) -> login.start passwordless -> /verify.
 *   - no existe -> propone crear la cuenta (login.start crea el user) -> /verify.
 *   - no disponible -> mensaje generico.
 *   Conserva el login con passkey (WebAuthnLoginButton).
 */
export function LoginForm() {
	const router = useRouter();
	const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
	const [stage, setStage] = useState<Stage>({ kind: "email" });
	const checkEmail = useCheckEmail();
	const loginStart = useLoginStart();
	const setTempToken = useAuthStore((s) => s.setTempToken);

	const emailForm = useForm<LoginInput>({
		resolver: zodResolver(loginSchema),
		defaultValues: { email: "" },
	});

	const passwordForm = useForm<PasswordStepValues>({
		resolver: zodResolver(passwordStepSchema),
		defaultValues: { password: "" },
	});

	const goToVerify = () => {
		router.push(`${ROUTES.auth.verify}?flow=login`);
	};

	const onCheckEmail = emailForm.handleSubmit((values) => {
		checkEmail.mutate(
			{
				email: values.email,
				cf_turnstile_response: turnstileToken ?? "",
			},
			{
				onSuccess: ({ data }) => {
					if (data.unavailable) {
						setStage({ kind: "unavailable" });
						return;
					}
					if (!data.exists) {
						setStage({ kind: "create", email: values.email });
						return;
					}
					if (data.has_password && !data.pending) {
						setStage({ kind: "password", email: values.email });
						return;
					}
					setStage({ kind: "passwordless", email: values.email });
				},
			},
		);
	});

	const startPasswordless = (email: string) => {
		loginStart.mutate(
			{ email, cf_turnstile_response: turnstileToken ?? "" },
			{ onSuccess: goToVerify },
		);
	};

	const onPasswordSubmit = (email: string) =>
		passwordForm.handleSubmit((values) => {
			loginStart.mutate(
				{
					email,
					password: values.password,
					cf_turnstile_response: turnstileToken ?? "",
				},
				{
					onSuccess: ({ data }) => {
						setTempToken(data.temp_token);
						goToVerify();
					},
					onError: (error) => {
						if (error instanceof ApiError && error.status === 401) {
							passwordForm.setError("password", {
								message: "Contrasena incorrecta",
							});
						}
					},
				},
			);
		});

	const checkingPending = checkEmail.isPending;
	const startPending = loginStart.isPending;

	return (
		<div className="space-y-4">
			{stage.kind === "unavailable" && (
				<Alert variant="destructive">
					<AlertTitle>No se puede iniciar sesion</AlertTitle>
					<AlertDescription>
						No se puede iniciar sesion con esta cuenta.
					</AlertDescription>
				</Alert>
			)}

			{stage.kind === "create" && (
				<Alert>
					<AlertTitle>No existe una cuenta con ese email</AlertTitle>
					<AlertDescription className="space-y-2">
						<p>Crear cuenta?</p>
						<Button
							type="button"
							className="w-full"
							data-testid="login-create-account"
							disabled={startPending}
							onClick={() => startPasswordless(stage.email)}
						>
							{startPending ? "Creando..." : "Crear cuenta"}
						</Button>
					</AlertDescription>
				</Alert>
			)}

			{stage.kind === "passwordless" && (
				<Alert>
					<AlertTitle>Te enviaremos un codigo</AlertTitle>
					<AlertDescription className="space-y-2">
						<p>Inicia sesion con un magic-link o un codigo a tu email.</p>
						<Button
							type="button"
							className="w-full"
							data-testid="login-passwordless"
							disabled={startPending}
							onClick={() => startPasswordless(stage.email)}
						>
							{startPending ? "Enviando..." : "Continuar"}
						</Button>
					</AlertDescription>
				</Alert>
			)}

			{stage.kind === "password" && (
				<Form {...passwordForm}>
					<form
						onSubmit={onPasswordSubmit(stage.email)}
						className="space-y-4"
						noValidate
					>
						<FormField
							control={passwordForm.control}
							name="password"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Contrasena</FormLabel>
									<FormControl>
										<Input
											type="password"
											autoComplete="current-password"
											data-testid="login-password"
											{...field}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<Button
							type="submit"
							className="w-full"
							data-testid="login-password-submit"
							disabled={startPending}
						>
							{startPending ? "Iniciando..." : "Iniciar sesion"}
						</Button>
					</form>
				</Form>
			)}

			{stage.kind === "email" && (
				<Form {...emailForm}>
					<form onSubmit={onCheckEmail} className="space-y-4" noValidate>
						<FormField
							control={emailForm.control}
							name="email"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Email</FormLabel>
									<FormControl>
										<Input
											type="email"
											autoComplete="email"
											placeholder="tu@email.com"
											data-testid="login-email"
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
							data-testid="login-submit"
							disabled={checkingPending || turnstileToken === null}
						>
							{checkingPending ? "Verificando..." : "Continuar"}
						</Button>
					</form>
				</Form>
			)}

			<WebAuthnLoginButton />
		</div>
	);
}
