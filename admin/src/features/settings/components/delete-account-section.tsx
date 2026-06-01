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
	AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/features/auth";
import { useDeleteAccount } from "../hooks/use-delete-account";

/**
 * @component DeleteAccountSection
 * @description Zona de peligro: elimina la cuenta. El AlertDialog exige
 *   re-tipear el email exacto antes de habilitar la accion. Confirmar dispara
 *   use-delete-account con el sentinel 'DELETE-MY-ACCOUNT'. Un 409
 *   CANNOT_DELETE_ADMIN_ACCOUNT NO redirige (lo maneja el hook).
 */
export function DeleteAccountSection() {
	const email = useAuthStore((s) => s.user?.email ?? "");
	const deleteAccount = useDeleteAccount();
	const [confirmEmail, setConfirmEmail] = useState("");
	const [open, setOpen] = useState(false);

	const matches = confirmEmail.trim() === email && email.length > 0;

	return (
		<Card className="border-destructive/40">
			<CardHeader>
				<CardTitle className="text-destructive">Eliminar mi cuenta</CardTitle>
				<CardDescription>
					Esta accion es permanente: anonimiza tus datos y cierra todas tus
					sesiones.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<AlertDialog
					open={open}
					onOpenChange={(next) => {
						setOpen(next);
						if (!next) setConfirmEmail("");
					}}
				>
					<AlertDialogTrigger asChild>
						<Button type="button" variant="destructive">
							Eliminar mi cuenta
						</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>Confirma la eliminacion</AlertDialogTitle>
							<AlertDialogDescription>
								Escribe tu email ({email}) para confirmar. No se puede deshacer.
							</AlertDialogDescription>
						</AlertDialogHeader>

						<div className="space-y-2">
							<Label htmlFor="delete-confirm-email">Tu email</Label>
							<Input
								id="delete-confirm-email"
								type="email"
								value={confirmEmail}
								onChange={(event) => setConfirmEmail(event.target.value)}
								placeholder={email}
							/>
						</div>

						<AlertDialogFooter>
							<AlertDialogCancel>Cancelar</AlertDialogCancel>
							<AlertDialogAction
								variant="destructive"
								disabled={!matches || deleteAccount.isPending}
								onClick={(event) => {
									// Evita que el AlertDialog cierre antes de la mutation.
									event.preventDefault();
									if (!matches) return;
									deleteAccount.mutate();
								}}
							>
								{deleteAccount.isPending ? "Eliminando..." : "Eliminar cuenta"}
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</CardContent>
		</Card>
	);
}
