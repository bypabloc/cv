"use client";

import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from "@/components/ui/alert-dialog";

/**
 * @component DeleteEntityDialog
 * @description AlertDialog de confirmacion del delete de una entidad del CV.
 *   Controlado por el slug en borrado (null = cerrado).
 *
 * @props {string | null} slug - Slug de la entidad a borrar (null cierra)
 * @props {boolean} pending - Mutation en vuelo (deshabilita confirmar)
 * @props {() => void} onConfirm - Confirmacion del borrado
 * @props {() => void} onCancel - Cancelar/cerrar
 */
interface DeleteEntityDialogProps {
	slug: string | null;
	pending: boolean;
	onConfirm: () => void;
	onCancel: () => void;
}

export function DeleteEntityDialog({
	slug,
	pending,
	onConfirm,
	onCancel,
}: DeleteEntityDialogProps) {
	return (
		// Sin trigger interno: Radix solo emite onOpenChange(false)
		// (Escape / overlay / Cancel), por eso cierra directo con onCancel.
		<AlertDialog open={slug !== null} onOpenChange={() => onCancel()}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>Eliminar entrada</AlertDialogTitle>
					<AlertDialogDescription>
						Se eliminara <span className="font-mono">{slug}</span> del CV
						(incluyendo sus traducciones, niches y prioridades). Esta accion no
						se puede deshacer.
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel data-testid="cv-entity-delete-cancel">
						Cancelar
					</AlertDialogCancel>
					<AlertDialogAction
						data-testid="cv-entity-delete-confirm"
						disabled={pending}
						onClick={onConfirm}
					>
						Eliminar
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	);
}
