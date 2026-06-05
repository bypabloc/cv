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
import { ROUTES } from "@/lib/routes";
import { type LoginInput, loginSchema } from "@/lib/validation/auth";
import type { MethodRequired } from "@/types/api";
import { useCheckEmail } from "../hooks/use-check-email";
import { useLoginStart } from "../hooks/use-login-start";
import { LoginChecklist } from "./login-checklist";
import { TurnstileWidget } from "./turnstile-widget";
import { WebAuthnLoginButton } from "./webauthn-login-button";

/** Estado de la maquina del flujo de login (paso 2 segun check-email). */
type Stage =
	| { kind: "email" }
	| { kind: "passwordless"; email: string }
	| { kind: "create"; email: string }
	| {
			kind: "checklist";
			email: string;
			methodsRequired: MethodRequired[];
			tempToken: string;
			pending?: string[];
	  }
	| { kind: "unavailable" };

/**
 * @component LoginForm
 * @description Login de 2 pasos. Paso 1: email + Turnstile -> login.check-email.
 *   Paso 2 segun el resultado:
 *   - existe con metodos `required` -> login.start (precheck, sin email) ->
 *     CHECKLIST: el user completa los factores en cualquier orden.
 *   - existe sin metodos (o pending) -> login.start passwordless -> /verify.
 *   - no existe -> propone crear la cuenta (login.start con email) -> /verify.
 *   - no disponible -> mensaje generico.
 *   Conserva el login con passkey passwordless (WebAuthnLoginButton).
 */
export function LoginForm() {
	const router = useRouter();
	const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
	// Temp JWT precheck (flow='login' step=0) que devuelve login.check-email
	// tras validar Turnstile. login.start lo manda en Authorization en vez del
	// captcha (el token de Turnstile es single-use: reusarlo daba
	// `timeout-or-duplicate`).
	const [precheckToken, setPrecheckToken] = useState<string | null>(null);
	const [stage, setStage] = useState<Stage>({ kind: "email" });
	const checkEmail = useCheckEmail();
	const loginStart = useLoginStart();

	const emailForm = useForm<LoginInput>({
		resolver: zodResolver(loginSchema),
		defaultValues: { email: "" },
	});

	const goToVerify = () => {
		router.push(`${ROUTES.auth.verify}?flow=login`);
	};

	/** login.start (precheck, sin email): emite el temp step=2 del checklist. */
	const startChecklist = (
		email: string,
		methodsRequired: MethodRequired[],
		precheck: string | null,
	) => {
		if (precheck === null) return;
		loginStart.mutate(
			{ precheckToken: precheck },
			{
				onSuccess: ({ data }) => {
					setStage({
						kind: "checklist",
						email,
						methodsRequired,
						tempToken: data.temp_token,
						pending: data.methods,
					});
				},
			},
		);
	};

	/** Alta fusionada / passwordless: login.start con (alta) o sin email. */
	const startPasswordless = (email: string, withEmail: boolean) => {
		if (precheckToken === null) return;
		loginStart.mutate(
			{ precheckToken, email: withEmail ? email : undefined },
			{ onSuccess: goToVerify },
		);
	};

	const onCheckEmail = emailForm.handleSubmit((values) => {
		checkEmail.mutate(
			{
				email: values.email,
				cf_turnstile_response: turnstileToken ?? "",
			},
			{
				onSuccess: ({ data }) => {
					// El precheck autoriza login.start. unavailable no trae temp
					// (no hay flujo que continuar) y ese stage no llama login.start.
					setPrecheckToken(data.temp_token ?? null);
					if (data.unavailable) {
						setStage({ kind: "unavailable" });
						return;
					}
					if (!data.exists) {
						setStage({ kind: "create", email: values.email });
						return;
					}
					const required = data.methods_required ?? [];
					if (data.pending || required.length === 0) {
						setStage({ kind: "passwordless", email: values.email });
						return;
					}
					startChecklist(values.email, required, data.temp_token ?? null);
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
							onClick={() => startPasswordless(stage.email, true)}
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
							onClick={() => startPasswordless(stage.email, false)}
						>
							{startPending ? "Enviando..." : "Continuar"}
						</Button>
					</AlertDescription>
				</Alert>
			)}

			{stage.kind === "checklist" && (
				<LoginChecklist
					methodsRequired={stage.methodsRequired}
					initialTempToken={stage.tempToken}
					email={stage.email}
					initialPending={stage.pending}
				/>
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

			{stage.kind === "email" && <WebAuthnLoginButton />}
		</div>
	);
}
