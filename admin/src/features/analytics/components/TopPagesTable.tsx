"use client";

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type { TopPageItem } from "../types";

/**
 * @component TopPagesTable
 * @description Ranking de paginas (analytics/top-pages): page_path + events +
 *   unique_visitors + unique_visits.
 *
 * @props {TopPageItem[]} items - filas del ranking
 */
export function TopPagesTable({ items }: { items: TopPageItem[] }) {
	if (items.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin paginas en el rango seleccionado.
			</p>
		);
	}
	return (
		<Table>
			<TableHeader>
				<TableRow>
					<TableHead>Pagina</TableHead>
					<TableHead className="text-right">Eventos</TableHead>
					<TableHead className="text-right">Visitantes</TableHead>
					<TableHead className="text-right">Visitas</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{items.map((item) => (
					<TableRow key={item.page_path}>
						<TableCell className="font-mono text-xs">
							{item.page_path}
						</TableCell>
						<TableCell className="text-right">{item.events}</TableCell>
						<TableCell className="text-right">{item.unique_visitors}</TableCell>
						<TableCell className="text-right">{item.unique_visits}</TableCell>
					</TableRow>
				))}
			</TableBody>
		</Table>
	);
}
