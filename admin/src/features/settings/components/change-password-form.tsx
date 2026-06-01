"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	Form,
	FormControl,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useChangePassword } from "../hooks/use-change-password";
import { type ChangePasswordInput, changePasswordSchema } from "../validation";

/**
 * @component ChangePasswordForm
 * @description Cambia la contrasena del usuario autenticado. Conecta a la
 *   action REAL `users.profile.change-password` (SIN flag de bloqueo, SIN
 *   aviso de "proximamente"). Zod refine: new >= 12 chars y new === confirm.
 */
export function ChangePasswordForm() {
	const changePassword = useChangePassword();

	const form = useForm<ChangePasswordInput>({
		resolver: zodResolver(changePasswordSchema),
		defaultValues: { current_password: "", new_password: "", confirm: "" },
	});

	const onSubmit = form.handleSubmit((values) => {
		changePassword.mutate(
			{
				current_password: values.current_password,
				new_password: values.new_password,
			},
			{
				onSuccess: () => {
					form.reset();
				},
			},
		);
	});

	return (
		<Card>
			<CardHeader>
				<CardTitle>Cambiar contrasena</CardTitle>
				<CardDescription>
					Ingresa tu contrasena actual y la nueva (minimo 12 caracteres).
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Form {...form}>
					<form onSubmit={onSubmit} className="space-y-4" noValidate>
						<FormField
							control={form.control}
							name="current_password"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Contrasena actual</FormLabel>
									<FormControl>
										<Input
											type="password"
											autoComplete="current-password"
											{...field}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>
						<FormField
							control={form.control}
							name="new_password"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Nueva contrasena</FormLabel>
									<FormControl>
										<Input
											type="password"
											autoComplete="new-password"
											{...field}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>
						<FormField
							control={form.control}
							name="confirm"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Confirmar nueva contrasena</FormLabel>
									<FormControl>
										<Input
											type="password"
											autoComplete="new-password"
											{...field}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<Button type="submit" disabled={changePassword.isPending}>
							{changePassword.isPending
								? "Actualizando..."
								: "Actualizar contrasena"}
						</Button>
					</form>
				</Form>
			</CardContent>
		</Card>
	);
}
