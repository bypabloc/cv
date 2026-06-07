"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/routes";
import type { MethodKind, MethodRequired, VerifyResult } from "@/types/api";
import { useLoginSendEmailCode } from "../hooks/use-login-send-email-code";
import { isAuthResponse } from "../lib/verify-result";
import { useAuthStore } from "../store/use-auth-store";
import { LoginMethodPicker } from "./login-method-picker";
import { LoginPasswordInput } from "./login-password-input";
import { LoginTotpInput } from "./login-totp-input";
import { RecoveryCodeInput } from "./recovery-code-input";
import { VerifyCodeInput } from "./verify-code-input";
import { WebAuthnLoginButton } from "./webauthn-login-button";

/** Etiqueta legible + alias que usa el `methods` del backend (vocabulario
 *  distinto al de `methods_required`) para reconciliar los pendientes. */
const METHOD_META: Record<MethodKind, { label: string; aliases: string[] }> = {
	password: { label: "Contrasena", aliases: ["password"] },
	passwordless: { label: "Codigo por email", aliases: ["magic-link"] },
	totp: { label: "Codigo TOTP", aliases: ["totp"] },
	email_code: { label: "Codigo por email", aliases: ["email-code"] },
	webauthn: { label: "Passkey", aliases: ["webauthn"] },
};

interface MethodState {
	type: MethodKind;
	satisfied: boolean;
}

/**
 * @function reconcilePending
 * @description Marca como satisfechos los metodos que el backend ya NO lista en
 *   `pending` (su `methods` post-verify). Un metodo sigue pendiente si su alias
 *   aparece en `pending`. Si `pending` es undefined, no toca nada (solo cuenta
 *   el metodo recien hecho como satisfecho).
 */
function reconcilePending(
	methods: MethodState[],
	pending: string[] | undefined,
): MethodState[] {
	if (pending === undefined) return methods;
	return methods.map((m) => {
		if (m.satisfied) return m;
		const stillPending = METHOD_META[m.type].aliases.some((a) =>
			pending.includes(a),
		);
		return stillPending ? m : { ...m, satisfied: true };
	});
}

/** Vista activa del checklist cuando hay >1 metodo: la lista selectora o el
 *  input de un metodo concreto. Con 1 metodo el input se muestra directo. */
type View = "list" | MethodKind;

/**
 * @component LoginChecklist
 * @description Checklist de metodos `required`: el user completa los factores
 *   en CUALQUIER orden. El `tempToken` es la fuente de verdad y es ROLLING:
 *   cada verify exitoso devuelve un temp_token NUEVO que reemplaza al anterior
 *   (el viejo se blacklistea -> reusarlo da TOKEN_BLACKLISTED). El login cierra
 *   cuando un verify devuelve un AuthResponse (`mfa_complete: true`).
 *
 *   UI segun la cantidad de metodos:
 *   - 1 metodo `required` -> su input directo (sin lista ni contador).
 *   - >1 metodos -> una LISTA selectora (icono + titulo + descripcion +
 *     chevron); al elegir uno se entra a su input + un boton "Atras"; al
 *     completar un factor se vuelve a la lista automaticamente.
 *
 * @props {MethodRequired[]} methodsRequired - lista de metodos del checklist
 * @props {string} initialTempToken - temp_token step=2 inicial (login.start)
 * @props {string} email - email del user (para el factor passkey)
 * @props {string[]} [initialPending] - metodos pendientes iniciales (`methods`)
 */
export function LoginChecklist({
	methodsRequired,
	initialTempToken,
	email,
	initialPending,
}: {
	methodsRequired: MethodRequired[];
	initialTempToken: string;
	email: string;
	initialPending?: string[];
}) {
	const router = useRouter();
	const setTokens = useAuthStore((s) => s.setTokens);
	const sendEmailCode = useLoginSendEmailCode();
	const [showRecovery, setShowRecovery] = useState(false);

	const [tempToken, setTempToken] = useState(initialTempToken);
	const [methods, setMethods] = useState<MethodState[]>(() =>
		reconcilePending(
			methodsRequired.map((m) => ({ type: m.type, satisfied: false })),
			initialPending,
		),
	);
	const [emailCodeSent, setEmailCodeSent] = useState<Record<string, boolean>>(
		() =>
			Object.fromEntries(methodsRequired.map((m) => [m.type, m.sent === true])),
	);

	// Con 1 solo metodo NO hay lista: el input se muestra directo (view fija en
	// ese metodo). Con >1 la view arranca en la lista selectora.
	const single = methodsRequired.length === 1;
	const [view, setView] = useState<View>(() =>
		single ? (methodsRequired[0]?.type ?? "list") : "list",
	);

	const completed = methods.filter((m) => m.satisfied).length;
	const total = methods.length;

	const onResult = (justDone: MethodKind) => (data: VerifyResult) => {
		if (isAuthResponse(data)) {
			// El cierre del checklist puede NO re-enviar el perfil (user
			// opcional): setTokens conserva el user actual cuando llega undefined
			// (el bootstrap/refresh lo hidrata).
			setTokens(data.access_token, data.refresh_token, data.user);
			router.replace(ROUTES.admin.root);
			toast.success("Sesion iniciada");
			return;
		}
		// Rolling: el temp_token nuevo reemplaza al anterior.
		setTempToken(data.temp_token);
		setMethods((prev) =>
			reconcilePending(
				prev.map((m) => (m.type === justDone ? { ...m, satisfied: true } : m)),
				data.methods,
			),
		);
		// Con >1 metodo, al completar un factor vuelve a la lista para elegir el
		// siguiente. Con 1 metodo no hay lista (el cierre lo maneja AuthResponse).
		if (!single) setView("list");
	};

	const onSendEmailCode = (type: MethodKind) => {
		sendEmailCode.mutate(
			{ temp_token: tempToken },
			{
				onSuccess: () => {
					setEmailCodeSent((prev) => ({ ...prev, [type]: true }));
				},
			},
		);
	};

	const renderInput = (type: MethodKind) => {
		switch (type) {
			case "password":
				return (
					<LoginPasswordInput
						tempToken={tempToken}
						onResult={onResult("password")}
						testid="checklist-password"
					/>
				);
			case "totp":
				return (
					<LoginTotpInput
						tempToken={tempToken}
						onResult={onResult("totp")}
						withRecovery={false}
						testid="checklist-totp"
					/>
				);
			case "email_code":
			case "passwordless":
				return (
					<div className="space-y-3">
						{!emailCodeSent[type] && (
							<Button
								type="button"
								variant="outline"
								className="w-full"
								data-testid="checklist-send-code"
								disabled={sendEmailCode.isPending}
								onClick={() => onSendEmailCode(type)}
							>
								{sendEmailCode.isPending ? "Enviando..." : "Enviar codigo"}
							</Button>
						)}
						<VerifyCodeInput
							tempToken={tempToken}
							onResult={onResult(type)}
							testid="checklist-email-code"
						/>
					</div>
				);
			case "webauthn":
				return (
					<WebAuthnLoginButton
						email={email}
						onResult={onResult("webauthn")}
						testid="checklist-webauthn"
						tempToken={tempToken}
					/>
				);
			default:
				return null;
		}
	};

	const recoveryLink = (
		<Button
			type="button"
			variant="link"
			className="w-full"
			data-testid="checklist-use-recovery"
			onClick={() => setShowRecovery(true)}
		>
			Usar codigo de recuperacion
		</Button>
	);

	if (showRecovery) {
		return (
			<div className="space-y-4" data-testid="login-checklist">
				<h2 className="font-semibold">Codigo de recuperacion</h2>
				<p className="text-sm text-muted-foreground">
					Saltea todos los metodos requeridos.
				</p>
				<RecoveryCodeInput
					tempToken={tempToken}
					onResult={onResult("password")}
					testid="checklist-recovery"
				/>
				<Button
					type="button"
					variant="link"
					className="w-full"
					onClick={() => setShowRecovery(false)}
				>
					Volver a los metodos
				</Button>
			</div>
		);
	}

	// 1 metodo `required`: el input directo (sin lista ni contador).
	if (single) {
		return (
			<div className="space-y-6" data-testid="login-checklist">
				<div className="space-y-2 rounded-lg border p-4">
					{renderInput(view as MethodKind)}
				</div>
				{recoveryLink}
			</div>
		);
	}

	// >1 metodos: la sub-vista del input de un metodo elegido (con "Atras").
	if (view !== "list") {
		return (
			<div className="space-y-4" data-testid="login-checklist">
				<Button
					type="button"
					variant="ghost"
					size="sm"
					className="-ml-2 gap-1"
					data-testid="checklist-back"
					onClick={() => setView("list")}
				>
					<ArrowLeft className="size-4" aria-hidden="true" />
					Atras
				</Button>
				<h2 className="font-semibold">{METHOD_META[view].label}</h2>
				{renderInput(view)}
				{recoveryLink}
			</div>
		);
	}

	// >1 metodos: la lista selectora.
	return (
		<div className="space-y-6" data-testid="login-checklist">
			<p
				className="text-sm text-muted-foreground"
				data-testid="checklist-progress"
			>
				{completed} de {total} completados
			</p>

			<LoginMethodPicker methods={methods} onSelect={(type) => setView(type)} />

			{recoveryLink}
		</div>
	);
}
