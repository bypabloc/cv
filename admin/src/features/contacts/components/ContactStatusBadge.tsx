"use client";

import { Badge } from "@/components/ui/badge";
import type { ContactStatus } from "../types";

/**
 * @component ContactStatusBadge
 * @description Badge del estado de un contacto con variante segun el estado
 *   del embudo (new -> converted = progreso, rejected = destructivo).
 *
 * @props {ContactStatus} status - estado del contacto
 */
type BadgeVariant = "default" | "secondary" | "outline" | "destructive";

const STATUS_LABEL: Record<ContactStatus, string> = {
	new: "Nuevo",
	contacted: "Contactado",
	qualified: "Calificado",
	converted: "Convertido",
	rejected: "Rechazado",
};

const STATUS_VARIANT: Record<ContactStatus, BadgeVariant> = {
	new: "default",
	contacted: "secondary",
	qualified: "secondary",
	converted: "default",
	rejected: "destructive",
};

export function ContactStatusBadge({ status }: { status: ContactStatus }) {
	return (
		<Badge variant={STATUS_VARIANT[status] ?? "outline"}>
			{STATUS_LABEL[status] ?? status}
		</Badge>
	);
}
