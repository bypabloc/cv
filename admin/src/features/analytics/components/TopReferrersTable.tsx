"use client";

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type { RankItem } from "../types";

/**
 * @component TopReferrersTable
 * @description Ranking generico (referrers o UTM) de analytics/top-referrers:
 *   etiqueta + visitas. La columna de etiqueta se resuelve del primer campo
 *   no-numerico presente en el item.
 *
 * @props {string} label - encabezado de la columna de etiqueta
 * @props {RankItem[]} items - filas del ranking
 */
function rowLabel(item: RankItem): string {
	return (
		item.referrer ??
		item.utm_source ??
		item.utm_medium ??
		item.utm_campaign ??
		"(desconocido)"
	);
}

export function TopReferrersTable({
	label,
	items,
}: {
	label: string;
	items: RankItem[];
}) {
	if (items.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin datos en el rango seleccionado.
			</p>
		);
	}
	return (
		<Table>
			<TableHeader>
				<TableRow>
					<TableHead>{label}</TableHead>
					<TableHead className="text-right">Visitas</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{items.map((item) => (
					<TableRow key={rowLabel(item)}>
						<TableCell className="font-mono text-xs">
							{rowLabel(item)}
						</TableCell>
						<TableCell className="text-right">{item.visits}</TableCell>
					</TableRow>
				))}
			</TableBody>
		</Table>
	);
}
