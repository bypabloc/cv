"use client";

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type { ContactStatusItem } from "../types";

/**
 * @component ContactByStatusTable
 * @description Desglose de contactos por estado (contacts/by-status): status +
 *   count + pct. Acompana al PieChart con el porcentaje exacto por fila.
 *
 * @props {ContactStatusItem[]} items - filas del desglose
 */
export function ContactByStatusTable({
	items,
}: {
	items: ContactStatusItem[];
}) {
	if (items.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin contactos en el rango seleccionado.
			</p>
		);
	}
	return (
		<Table>
			<TableHeader>
				<TableRow>
					<TableHead>Estado</TableHead>
					<TableHead className="text-right">Cantidad</TableHead>
					<TableHead className="text-right">%</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{items.map((item) => (
					<TableRow key={item.status}>
						<TableCell className="font-mono text-xs">{item.status}</TableCell>
						<TableCell className="text-right">{item.count}</TableCell>
						<TableCell className="text-right">
							{(item.pct * 100).toFixed(1)}%
						</TableCell>
					</TableRow>
				))}
			</TableBody>
		</Table>
	);
}
