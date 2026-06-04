"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { ErrorAlert } from "@/components/ui/error-alert";
import {
	Form,
	FormControl,
	FormDescription,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useProfile } from "../hooks/use-profile";
import { useUpdateProfile } from "../hooks/use-update-profile";
import { type ProfileInput, profileSchema } from "../validation";

/**
 * @component ProfileForm
 * @description Perfil del usuario: `email` read-only (de users.profile.get) +
 *   `display_name` editable. react-hook-form + Zod -> users.profile.update.
 */
export function ProfileForm() {
	const profile = useProfile();
	const updateProfile = useUpdateProfile();

	const form = useForm<ProfileInput>({
		resolver: zodResolver(profileSchema),
		defaultValues: { display_name: "" },
	});

	// Hidrata el form UNA sola vez con la data del backend. Sin el guard, el
	// reset se dispara en cada render (profile.data cambia de referencia con
	// Tanstack) y pisa lo que el usuario tipea en "Nombre para mostrar".
	const { reset } = form;
	const hydrated = useRef(false);
	const displayName = profile.data?.display_name;
	useEffect(() => {
		if (profile.data && !hydrated.current) {
			reset({ display_name: displayName ?? "" });
			hydrated.current = true;
		}
	}, [profile.data, displayName, reset]);

	if (profile.isLoading) {
		return <LoadingSpinner />;
	}

	if (profile.isError || !profile.data) {
		return (
			<ErrorAlert error={profile.error} onRetry={() => profile.refetch()} />
		);
	}

	const onSubmit = form.handleSubmit((values) => {
		updateProfile.mutate({ display_name: values.display_name });
	});

	return (
		<Form {...form}>
			<form onSubmit={onSubmit} className="space-y-4" noValidate>
				<div className="space-y-2">
					<Label htmlFor="settings-email">Email</Label>
					<Input
						id="settings-email"
						type="email"
						value={profile.data.email}
						readOnly
						disabled
					/>
					<p className="text-sm text-muted-foreground">
						Para cambiar tu email usa la seccion de abajo.
					</p>
				</div>

				<FormField
					control={form.control}
					name="display_name"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Nombre para mostrar</FormLabel>
							<FormControl>
								<Input autoComplete="name" {...field} />
							</FormControl>
							<FormDescription>
								Asi te identificaremos en el panel.
							</FormDescription>
							<FormMessage />
						</FormItem>
					)}
				/>

				<Button type="submit" disabled={updateProfile.isPending}>
					{updateProfile.isPending ? "Guardando..." : "Guardar cambios"}
				</Button>
			</form>
		</Form>
	);
}
