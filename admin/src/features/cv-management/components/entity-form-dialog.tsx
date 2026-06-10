"use client";

import type { ReactNode } from "react";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";

/**
 * @component EntityFormDialog
 * @description Dialog generico de alta/edicion de una entidad del CV. El
 *   form hijo se re-monta por entidad (el caller lo keyea por slug) para
 *   que los defaults hidraten correcto.
 *
 * @props {boolean} open - Estado controlado del dialog
 * @props {(open: boolean) => void} onOpenChange - Cierre/apertura
 * @props {string} title - Titulo del dialog
 * @props {string} [description] - Descripcion bajo el titulo
 * @props {ReactNode} children - El form de la entidad
 */
interface EntityFormDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	title: string;
	description?: string;
	children: ReactNode;
}

export function EntityFormDialog({
	open,
	onOpenChange,
	title,
	description,
	children,
}: EntityFormDialogProps) {
	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent
				className="max-h-[85vh] overflow-y-auto sm:max-w-2xl"
				data-testid="cv-entity-form-dialog"
			>
				<DialogHeader>
					<DialogTitle>{title}</DialogTitle>
					{description ? (
						<DialogDescription>{description}</DialogDescription>
					) : null}
				</DialogHeader>
				{children}
			</DialogContent>
		</Dialog>
	);
}
