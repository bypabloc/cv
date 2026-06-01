"use client";

import { SetPasswordForm } from "@/features/auth/components/set-password-form";

/**
 * @page SetPasswordPage
 * @description Pagina de set-password del onboarding (ruta `/set-password`).
 */
export default function SetPasswordPage() {
	return (
		<div className="flex min-h-screen flex-col items-center justify-center p-6">
			<div className="w-full max-w-sm space-y-6">
				<h1 className="text-2xl font-bold">Crea tu contrasena</h1>
				<SetPasswordForm />
			</div>
		</div>
	);
}
