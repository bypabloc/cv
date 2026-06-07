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
import {
	type ChangePasswordInput,
	changePasswordSchema,
	type SetPasswordInput,
	setPasswordSchema,
} from "../validation";

/**
 * @component ChangePasswordForm
 * @description Cambia o ESTABLECE la contrasena del usuario autenticado contra
 *   la action REAL `users.profile.change-password`. Si `hasPassword` es false
 *   (user passwordless): titulo "Establecer contrasena", SIN campo "contrasena
 *   actual", y al enviar omite current_password. Si es true: flujo de cambio
 *   con la actual. Zod refine: new >= 12 chars y new === confirm.
 *
 * @props {boolean} [hasPassword] - true si el user ya tiene contrasena seteada.
 */
export function ChangePasswordForm({
	hasPassword = true,
}: {
	hasPassword?: boolean;
}) {
	return hasPassword ? <ChangeMode /> : <SetMode />;
}

function ChangeMode() {
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
			{ onSuccess: () => form.reset() },
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

function SetMode() {
	const changePassword = useChangePassword();
	const form = useForm<SetPasswordInput>({
		resolver: zodResolver(setPasswordSchema),
		defaultValues: { new_password: "", confirm: "" },
	});

	const onSubmit = form.handleSubmit((values) => {
		// Passwordless: omitimos current_password (el backend lo acepta).
		changePassword.mutate(
			{ new_password: values.new_password },
			{ onSuccess: () => form.reset() },
		);
	});

	return (
		<Card>
			<CardHeader>
				<CardTitle>Establecer contrasena</CardTitle>
				<CardDescription>
					Aun no tienes contrasena. Crea una (minimo 12 caracteres) para poder
					iniciar sesion con ella.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Form {...form}>
					<form onSubmit={onSubmit} className="space-y-4" noValidate>
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
								? "Guardando..."
								: "Establecer contrasena"}
						</Button>
					</form>
				</Form>
			</CardContent>
		</Card>
	);
}
