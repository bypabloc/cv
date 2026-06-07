"use client";

import { useState } from "react";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { TotpSetup, WebAuthnRegisterButton } from "@/features/auth";
import type {
	MfaKind,
	SecurityMethod,
	SecurityMethodType,
	SecurityPasskey,
} from "@/types/models";
import { useSecurityOverview } from "../hooks/use-security-overview";
import { useSetRequired } from "../hooks/use-set-required";
import { useToggleMethod } from "../hooks/use-toggle-method";
import { ChangePasswordForm } from "./change-password-form";
import { RecoveryCodesSection } from "./recovery-codes-section";

/**
 * @function asPasskeys
 * @description Extrae el array de passkeys del `detail` polimorfico de un
 *   SecurityMethod type 'webauthn' con narrow (sin `any`). Devuelve [] si el
 *   shape no coincide.
 */
function asPasskeys(detail: Record<string, unknown>): SecurityPasskey[] {
	const credentials = detail.credentials;
	return Array.isArray(credentials) ? (credentials as SecurityPasskey[]) : [];
}

/**
 * @function asNumber
 * @description Lee un campo numerico del `detail` con narrow. Devuelve 0 si no
 *   es number.
 */
function asNumber(detail: Record<string, unknown>, key: string): number {
	const value = detail[key];
	return typeof value === "number" ? value : 0;
}

/**
 * @function asString
 * @description Lee un campo string del `detail` con narrow. Devuelve null si no
 *   es string.
 */
function asString(detail: Record<string, unknown>, key: string): string | null {
	const value = detail[key];
	return typeof value === "string" ? value : null;
}

/**
 * @function StatusBadge
 * @description Badge de estado de un metodo: 'No configurado' / 'Activo' /
 *   'Desactivado' segun configured + enabled.
 */
function StatusBadge({ method }: { method: SecurityMethod }) {
	if (!method.configured) {
		return <Badge variant="outline">No configurado</Badge>;
	}
	return method.enabled ? (
		<Badge variant="secondary">Activo</Badge>
	) : (
		<Badge variant="outline">Desactivado</Badge>
	);
}

/**
 * @function RequiredSwitch
 * @description Switch 'Requerido al loguear' con AlertDialog de advertencia al
 *   activar. Confirmar dispara `onConfirm(true)`; desactivar es directo.
 */
function RequiredSwitch({
	required,
	disabled,
	onConfirm,
}: {
	required: boolean;
	disabled: boolean;
	onConfirm: (required: boolean) => void;
}) {
	const [warnOpen, setWarnOpen] = useState(false);

	return (
		<>
			<span className="flex items-center gap-2 text-xs text-muted-foreground">
				<span>Requerido al loguear</span>
				<Switch
					size="sm"
					checked={required}
					disabled={disabled}
					onCheckedChange={(next) => {
						if (next) {
							setWarnOpen(true);
						} else {
							onConfirm(false);
						}
					}}
				/>
			</span>
			<AlertDialog open={warnOpen} onOpenChange={setWarnOpen}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Hacer obligatorio este metodo</AlertDialogTitle>
						<AlertDialogDescription>
							Guarda tus codigos de recuperacion; si pierdes este metodo solo
							entraras con un recovery code.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancelar</AlertDialogCancel>
						<AlertDialogAction
							onClick={() => {
								setWarnOpen(false);
								onConfirm(true);
							}}
						>
							Confirmar
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</>
	);
}

/**
 * @function PasskeyRow
 * @description Sub-fila de un passkey WebAuthn: nickname + Switch on/off +
 *   Switch requerido + boton Eliminar.
 */
function PasskeyRow({
	passkey,
	onToggle,
	onRequired,
	onDelete,
	toggling,
	settingRequired,
	deleting,
}: {
	passkey: SecurityPasskey;
	onToggle: (recordId: string, enable: boolean) => void;
	onRequired: (recordId: string, required: boolean) => void;
	onDelete: (recordId: string) => void;
	toggling: boolean;
	settingRequired: boolean;
	deleting: boolean;
}) {
	return (
		<li className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3">
			<span className="text-sm font-medium">
				{passkey.nickname ?? "Passkey"}
			</span>
			<div className="flex flex-wrap items-center gap-3">
				<span className="flex items-center gap-2 text-xs text-muted-foreground">
					<span>Activo</span>
					<Switch
						size="sm"
						checked={passkey.enabled}
						disabled={toggling}
						onCheckedChange={(next) => onToggle(passkey.credential_id, next)}
					/>
				</span>
				<RequiredSwitch
					required={passkey.required}
					disabled={settingRequired}
					onConfirm={(required) => onRequired(passkey.credential_id, required)}
				/>
				<Button
					type="button"
					variant="destructive"
					size="sm"
					disabled={deleting}
					onClick={() => onDelete(passkey.credential_id)}
				>
					Eliminar
				</Button>
			</div>
		</li>
	);
}

/**
 * @function WebauthnRow
 * @description Fila del metodo webauthn: estado + expansion de cada passkey.
 *   El boton 'Eliminar' por passkey se omite si no se provee onDelete.
 */
function WebauthnRow({
	method,
	onToggle,
	onRequired,
	toggling,
	settingRequired,
}: {
	method: SecurityMethod;
	onToggle: (vars: {
		type: SecurityMethodType;
		recordId: string;
		enable: boolean;
	}) => void;
	onRequired: (vars: {
		type: SecurityMethodType;
		recordId: string;
		required: boolean;
	}) => void;
	toggling: boolean;
	settingRequired: boolean;
}) {
	const passkeys = asPasskeys(method.detail);

	return (
		<div className="space-y-3 rounded-md border p-4">
			<div className="flex items-center justify-between gap-3">
				<span className="text-sm font-medium">{method.label}</span>
				<StatusBadge method={method} />
			</div>
			{passkeys.length === 0 ? (
				<p className="text-sm text-muted-foreground">
					No tienes passkeys registrados.
				</p>
			) : (
				<ul className="space-y-2">
					{passkeys.map((passkey) => (
						<PasskeyRow
							key={passkey.credential_id}
							passkey={passkey}
							toggling={toggling}
							settingRequired={settingRequired}
							deleting={false}
							onToggle={(recordId, enable) =>
								onToggle({ type: "webauthn", recordId, enable })
							}
							onRequired={(recordId, required) =>
								onRequired({ type: "webauthn", recordId, required })
							}
							onDelete={() => undefined}
						/>
					))}
				</ul>
			)}
			{/* Registrar un passkey nuevo (navigator.credentials.create via
			    webauthn.register-options -> register-verify). */}
			<WebAuthnRegisterButton />
		</div>
	);
}

/**
 * @function MfaRow
 * @description Fila de un metodo MFA (totp / email_code): estado + Switch on/off
 *   + Switch requerido. Si no esta configurado, muestra un boton 'Configurar'.
 */
function MfaRow({
	method,
	onToggle,
	onRequired,
	onConfigure,
	toggling,
	settingRequired,
}: {
	method: SecurityMethod;
	onToggle: (vars: {
		type: SecurityMethodType;
		kind: MfaKind;
		enable: boolean;
	}) => void;
	onRequired: (vars: {
		type: SecurityMethodType;
		kind: MfaKind;
		required: boolean;
	}) => void;
	onConfigure: (type: SecurityMethodType) => void;
	toggling: boolean;
	settingRequired: boolean;
}) {
	const kind = method.type as MfaKind;

	return (
		<div className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-4">
			<div className="flex items-center gap-2">
				<span className="text-sm font-medium">{method.label}</span>
				{method.preferred ? <Badge variant="secondary">Preferido</Badge> : null}
				<StatusBadge method={method} />
			</div>
			{method.configured ? (
				<div className="flex flex-wrap items-center gap-3">
					<span className="flex items-center gap-2 text-xs text-muted-foreground">
						<span>Activo</span>
						<Switch
							size="sm"
							checked={method.enabled}
							disabled={toggling}
							onCheckedChange={(next) =>
								onToggle({ type: method.type, kind, enable: next })
							}
						/>
					</span>
					<RequiredSwitch
						required={method.required}
						disabled={settingRequired}
						onConfirm={(required) =>
							onRequired({ type: method.type, kind, required })
						}
					/>
				</div>
			) : (
				<Button
					type="button"
					variant="outline"
					size="sm"
					onClick={() => onConfigure(method.type)}
				>
					Configurar
				</Button>
			)}
		</div>
	);
}

/**
 * @function RecoveryCodesRow
 * @description Fila de recovery_codes: muestra total/remaining + el generador.
 */
function RecoveryCodesRow({ method }: { method: SecurityMethod }) {
	const total = asNumber(method.detail, "total");
	const remaining = asNumber(method.detail, "remaining");

	return (
		<div className="space-y-3 rounded-md border p-4">
			<div className="flex items-center justify-end gap-3">
				<p className="mr-auto text-sm text-muted-foreground">
					Codigos disponibles: {remaining} de {total}.
				</p>
				<StatusBadge method={method} />
			</div>
			<RecoveryCodesSection />
		</div>
	);
}

/**
 * @function PasswordRow
 * @description Fila de password: muestra ultimo cambio + Switch 'Requerido al
 *   loguear' (security.password-set-required) + boton 'Cambiar contrasena' que
 *   abre el ChangePasswordForm en un Dialog. El Switch solo aparece si el user
 *   ya tiene contrasena configurada (no hay flag required sin password).
 */
function PasswordRow({
	method,
	onRequired,
	settingRequired,
}: {
	method: SecurityMethod;
	onRequired: (vars: { type: SecurityMethodType; required: boolean }) => void;
	settingRequired: boolean;
}) {
	const [open, setOpen] = useState(false);
	const lastChange = asString(method.detail, "last_change_at");
	// configured=true => el user ya tiene contrasena seteada.
	const hasPassword = method.configured;
	const cta = hasPassword ? "Cambiar contrasena" : "Establecer contrasena";

	return (
		<div
			data-testid="security-row-password"
			className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-4"
		>
			<div className="space-y-0.5">
				<div className="flex items-center gap-2">
					<span className="text-sm font-medium">{method.label}</span>
					<StatusBadge method={method} />
				</div>
				{lastChange ? (
					<p className="text-xs text-muted-foreground">
						Ultimo cambio: {lastChange}
					</p>
				) : null}
			</div>
			<div className="flex flex-wrap items-center gap-3">
				{hasPassword ? (
					<RequiredSwitch
						required={method.required}
						disabled={settingRequired}
						onConfirm={(required) =>
							onRequired({ type: method.type, required })
						}
					/>
				) : null}
				<Button
					type="button"
					variant="outline"
					size="sm"
					onClick={() => setOpen(true)}
				>
					{cta}
				</Button>
			</div>
			<Dialog open={open} onOpenChange={setOpen}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>{cta}</DialogTitle>
						<DialogDescription>
							{hasPassword
								? "Ingresa tu contrasena actual y la nueva."
								: "Aun no tienes contrasena. Crea una para iniciar sesion con ella."}
						</DialogDescription>
					</DialogHeader>
					<ChangePasswordForm hasPassword={hasPassword} />
				</DialogContent>
			</Dialog>
		</div>
	);
}

/**
 * @component SecurityOverviewPanel
 * @description Panel unificado de seguridad. Una sola query (security.overview)
 *   alimenta las 5 filas (totp, email_code, webauthn, recovery_codes,
 *   password). Cada metodo se renderiza segun su `type` con su Switch on/off
 *   (mediante useToggleMethod) y su control 'Requerido al loguear' (mediante
 *   useSetRequired, con AlertDialog de advertencia). El guard 409 lo maneja
 *   cada hook (toast + el Switch revierte por la invalidacion).
 */
export function SecurityOverviewPanel() {
	const overview = useSecurityOverview();
	const toggle = useToggleMethod();
	const setRequired = useSetRequired();
	const [setupKind, setSetupKind] = useState<MfaKind | null>(null);

	if (overview.isLoading) {
		return (
			<Card>
				<CardHeader>
					<CardTitle>Metodos de seguridad</CardTitle>
				</CardHeader>
				<CardContent className="space-y-3">
					<Skeleton className="h-16 w-full" />
					<Skeleton className="h-16 w-full" />
					<Skeleton className="h-16 w-full" />
				</CardContent>
			</Card>
		);
	}

	if (overview.isError || !overview.data) {
		return (
			<ErrorAlert error={overview.error} onRetry={() => overview.refetch()} />
		);
	}

	// email_code NO se lista: es el canal de entrada del login (siempre
	// disponible), no un metodo configurable desde el panel de seguridad.
	const methods = overview.data.methods.filter(
		(method) => method.type !== "email_code",
	);

	return (
		<Card>
			<CardHeader>
				<CardTitle>Metodos de seguridad</CardTitle>
				<CardDescription>
					Activa, desactiva o marca como requerido cada metodo. Debes conservar
					al menos uno activo.
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				{methods.map((method, index) => (
					<div key={method.type} className="space-y-4">
						{index > 0 ? <Separator /> : null}
						{method.type === "webauthn" ? (
							<WebauthnRow
								method={method}
								toggling={toggle.isPending}
								settingRequired={setRequired.isPending}
								onToggle={(vars) => toggle.mutate(vars)}
								onRequired={(vars) => setRequired.mutate(vars)}
							/>
						) : method.type === "recovery_codes" ? (
							<RecoveryCodesRow method={method} />
						) : method.type === "password" ? (
							<PasswordRow
								method={method}
								settingRequired={setRequired.isPending}
								onRequired={(vars) => setRequired.mutate(vars)}
							/>
						) : (
							<MfaRow
								method={method}
								toggling={toggle.isPending}
								settingRequired={setRequired.isPending}
								onToggle={(vars) => toggle.mutate(vars)}
								onRequired={(vars) => setRequired.mutate(vars)}
								onConfigure={(type) => setSetupKind(type as MfaKind)}
							/>
						)}
					</div>
				))}
			</CardContent>

			<Dialog
				open={setupKind === "totp"}
				onOpenChange={(open) => {
					if (!open) setSetupKind(null);
				}}
			>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Configurar TOTP</DialogTitle>
						<DialogDescription>
							Escanea el QR con tu app de autenticacion y confirma el codigo.
						</DialogDescription>
					</DialogHeader>
					<TotpSetup />
				</DialogContent>
			</Dialog>
		</Card>
	);
}
