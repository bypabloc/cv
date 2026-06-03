"use client";

import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import type { ContactStatus } from "../types";

/**
 * @component ContactStatusFilter
 * @description Select para filtrar el listado de contactos por estado. El
 *   valor `all` (centinela del UI) significa "sin filtro" y se mapea a
 *   `undefined` hacia el backend.
 *
 * @props {ContactStatus | undefined} value - estado seleccionado (o sin filtro)
 * @props {(status: ContactStatus | undefined) => void} onChange - callback
 */
const ALL = "all";

const STATUS_OPTIONS: readonly { value: ContactStatus; label: string }[] = [
	{ value: "new", label: "Nuevo" },
	{ value: "contacted", label: "Contactado" },
	{ value: "qualified", label: "Calificado" },
	{ value: "converted", label: "Convertido" },
	{ value: "rejected", label: "Rechazado" },
];

export function ContactStatusFilter({
	value,
	onChange,
}: {
	value: ContactStatus | undefined;
	onChange: (status: ContactStatus | undefined) => void;
}) {
	return (
		<Select
			value={value ?? ALL}
			onValueChange={(next) =>
				onChange(next === ALL ? undefined : (next as ContactStatus))
			}
		>
			<SelectTrigger size="sm" className="w-44">
				<SelectValue placeholder="Todos los estados" />
			</SelectTrigger>
			<SelectContent>
				<SelectItem value={ALL}>Todos los estados</SelectItem>
				{STATUS_OPTIONS.map((opt) => (
					<SelectItem key={opt.value} value={opt.value}>
						{opt.label}
					</SelectItem>
				))}
			</SelectContent>
		</Select>
	);
}
