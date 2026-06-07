"use client";

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type { EventDistributionItem } from "../types";

/**
 * @component EventDistributionTable
 * @description Ranking de tipos de evento (events/distribution): event_type +
 *   count + pct. Acompana al BarChart con el porcentaje exacto por fila.
 *
 * @props {EventDistributionItem[]} items - filas del ranking
 */
export function EventDistributionTable({
	items,
}: {
	items: EventDistributionItem[];
}) {
	if (items.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin eventos en el rango seleccionado.
			</p>
		);
	}
	return (
		<Table>
			<TableHeader>
				<TableRow>
					<TableHead>Tipo de evento</TableHead>
					<TableHead className="text-right">Cantidad</TableHead>
					<TableHead className="text-right">%</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{items.map((item) => (
					<TableRow key={item.event_type}>
						<TableCell className="font-mono text-xs">
							{item.event_type}
						</TableCell>
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
