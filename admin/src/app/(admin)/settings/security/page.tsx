"use client";

import { SecurityOverviewPanel } from "@/features/settings";

/**
 * @page SecuritySettingsPage
 * @description Tab "Seguridad" de /settings (los tabs viven en el layout).
 *   Panel unificado de metodos (security.overview) con una sola query. Cada
 *   metodo (TOTP, passkeys WebAuthn, codigos de recuperacion, contrasena) se
 *   activa/desactiva y se marca como requerido desde el mismo listado. El
 *   email-code NO se lista aqui (es el canal de entrada del login).
 */
export default function SecuritySettingsPage() {
	return (
		<div className="space-y-6">
			<SecurityOverviewPanel />
		</div>
	);
}
