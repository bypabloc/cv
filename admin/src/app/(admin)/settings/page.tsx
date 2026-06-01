"use client";

import { Suspense } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
	ChangeEmailForm,
	ConfirmEmailChange,
	DeleteAccountSection,
	ProfileForm,
} from "@/features/settings";

/**
 * @page SettingsPage
 * @description Configuracion de la cuenta. Tab Perfil (ProfileForm +
 *   ChangeEmailForm + confirmacion deep-link) + Tab Cuenta (DeleteAccountSection).
 *   ConfirmEmailChange lee `?token` via useSearchParams -> Suspense boundary.
 */
export default function SettingsPage() {
	return (
		<section className="mx-auto max-w-2xl space-y-6">
			<h1 className="text-2xl font-semibold">Configuracion</h1>

			<Tabs defaultValue="profile">
				<TabsList>
					<TabsTrigger value="profile">Perfil</TabsTrigger>
					<TabsTrigger value="account">Cuenta</TabsTrigger>
				</TabsList>

				<TabsContent value="profile" className="space-y-6">
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
				</TabsContent>

				<TabsContent value="account" className="space-y-6">
					<DeleteAccountSection />
				</TabsContent>
			</Tabs>
		</section>
	);
}
