"use client";

import { Suspense } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
	ChangeEmailForm,
	ConfirmEmailChange,
	DeleteAccountSection,
	ProfileForm,
} from "@/features/settings";

/**
 * @page SettingsProfilePage
 * @description Tab "Perfil y cuenta" de /settings (los tabs viven en el
 *   layout). Perfil (ProfileForm) + cambio de email + confirmacion deep-link +
 *   eliminar cuenta. ConfirmEmailChange lee `?token` -> Suspense boundary.
 */
export default function SettingsProfilePage() {
	return (
		<div className="space-y-6">
			<Suspense fallback={null}>
				<ConfirmEmailChange />
			</Suspense>
			<Card>
				<CardHeader>
					<CardTitle>Perfil</CardTitle>
				</CardHeader>
				<CardContent>
					<ProfileForm />
				</CardContent>
			</Card>
			<ChangeEmailForm />
			<DeleteAccountSection />
		</div>
	);
}
