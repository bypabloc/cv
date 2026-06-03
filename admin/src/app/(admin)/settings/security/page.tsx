"use client";

import { SecurityOverviewPanel } from "@/features/settings";

/**
 * @page SecuritySettingsPage
 * @description Seguridad de la cuenta: panel unificado de metodos (security.
 *   overview) con una sola query. Cada metodo (TOTP, email-code, passkeys
 *   WebAuthn, codigos de recuperacion, contrasena) se activa/desactiva y se
 *   marca como requerido desde el mismo listado. El cambio de contrasena y la
 *   generacion de recovery codes siguen accesibles desde sus filas.
 */
export default function SecuritySettingsPage() {
	return (
		<section className="mx-auto max-w-2xl space-y-6">
			<h1 className="text-2xl font-semibold">Seguridad</h1>

			<SecurityOverviewPanel />
		</section>
	);
}
