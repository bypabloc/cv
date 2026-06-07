"use client";

import {
	CheckCircle2,
	ChevronRight,
	Fingerprint,
	KeyRound,
	type LucideIcon,
	Mail,
	Smartphone,
} from "lucide-react";
import type { MethodKind } from "@/types/api";

/**
 * Metadata de render por metodo: icono + titulo + descripcion. El vocabulario
 * (titulo/descripcion) es el que ve el user al elegir el factor en la lista,
 * estilo "Elige un metodo de verificacion".
 */
const METHOD_RENDER: Record<
	MethodKind,
	{ icon: LucideIcon; label: string; description: string }
> = {
	password: {
		icon: KeyRound,
		label: "Contrasena",
		description: "Ingresaras tu contrasena.",
	},
	passwordless: {
		icon: Mail,
		label: "Codigo por email",
		description: "Te enviaremos un codigo a tu correo.",
	},
	email_code: {
		icon: Mail,
		label: "Codigo por email",
		description: "Te enviaremos un codigo a tu correo.",
	},
	totp: {
		icon: Smartphone,
		label: "Codigo TOTP",
		description: "Ingresaras el codigo de tu app de autenticacion.",
	},
	webauthn: {
		icon: Fingerprint,
		label: "Passkey",
		description: "Usa tu huella, rostro o llave de seguridad.",
	},
};

/** Un metodo de la lista, con su estado de completado. */
export interface PickerMethod {
	type: MethodKind;
	satisfied: boolean;
}

/**
 * @component LoginMethodPicker
 * @description Lista selectora de los metodos `required` del login (estilo
 *   "Elige un metodo de verificacion"). Una fila por metodo: icono + titulo +
 *   descripcion + chevron. Las filas completadas muestran un check y quedan
 *   deshabilitadas (no accionables). Presentacional puro: no conoce el
 *   tempToken ni los verifies; solo emite `onSelect(type)` al elegir un metodo
 *   pendiente.
 *
 * @props {PickerMethod[]} methods - los metodos `required` con su estado
 * @props {(type: MethodKind) => void} onSelect - callback al elegir uno pendiente
 */
export function LoginMethodPicker({
	methods,
	onSelect,
}: {
	methods: PickerMethod[];
	onSelect: (type: MethodKind) => void;
}) {
	return (
		<ul className="space-y-3" data-testid="login-method-picker">
			{methods.map((method) => {
				const meta = METHOD_RENDER[method.type];
				const Icon = meta.icon;
				return (
					<li key={method.type}>
						<button
							type="button"
							disabled={method.satisfied}
							aria-disabled={method.satisfied}
							data-testid={`picker-method-${method.type}`}
							onClick={() => onSelect(method.type)}
							className="flex w-full items-center gap-4 rounded-lg border p-4 text-left transition-colors hover:bg-accent disabled:cursor-default disabled:opacity-60 disabled:hover:bg-transparent"
						>
							<span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
								<Icon className="size-5" aria-hidden="true" />
							</span>
							<span className="flex-1 space-y-0.5">
								<span className="block font-medium">{meta.label}</span>
								<span className="block text-sm text-muted-foreground">
									{meta.description}
								</span>
							</span>
							{method.satisfied ? (
								<CheckCircle2
									className="size-5 shrink-0 text-muted-foreground"
									aria-label="Completado"
								/>
							) : (
								<ChevronRight
									className="size-5 shrink-0 text-muted-foreground"
									aria-hidden="true"
								/>
							)}
						</button>
					</li>
				);
			})}
		</ul>
	);
}
