"use client";

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type { GeoCountryItem } from "../types";

/**
 * @component GeoCountryTable
 * @description Ranking de paises (geo/by-country): country (ISO-2) + sessions +
 *   visits + events. Las filas llegan ya ordenadas por sessions desc del
 *   backend; igual se reordena en cliente para robustez.
 *
 * @props {GeoCountryItem[]} items - filas del ranking
 */
function fmtInt(v: number): string {
	return new Intl.NumberFormat("es").format(Math.round(v));
}

export function GeoCountryTable({ items }: { items: GeoCountryItem[] }) {
	if (items.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin paises en el rango seleccionado.
			</p>
		);
	}
	const rows = [...items].sort((a, b) => b.sessions - a.sessions);
	return (
		<Table>
			<TableHeader>
				<TableRow>
					<TableHead>Pais</TableHead>
					<TableHead className="text-right">Sesiones</TableHead>
					<TableHead className="text-right">Visitas</TableHead>
					<TableHead className="text-right">Eventos</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{rows.map((item) => (
					<TableRow key={item.country}>
						<TableCell className="font-mono text-xs uppercase">
							{item.country}
						</TableCell>
						<TableCell className="text-right">
							{fmtInt(item.sessions)}
						</TableCell>
						<TableCell className="text-right">{fmtInt(item.visits)}</TableCell>
						<TableCell className="text-right">{fmtInt(item.events)}</TableCell>
					</TableRow>
				))}
			</TableBody>
		</Table>
	);
}
