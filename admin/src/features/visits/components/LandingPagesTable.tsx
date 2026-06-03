"use client";

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type { LandingPageItem } from "../types";

/**
 * @component LandingPagesTable
 * @description Ranking de landing pages (visits/landing-pages): landing_page_path
 *   + visits + unique_visitors, ordenado por visits desc (el backend ya lo
 *   entrega ordenado).
 *
 * @props {LandingPageItem[]} items - filas del ranking
 */
export function LandingPagesTable({ items }: { items: LandingPageItem[] }) {
	if (items.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin landing pages en el rango seleccionado.
			</p>
		);
	}
	return (
		<Table>
			<TableHeader>
				<TableRow>
					<TableHead>Landing page</TableHead>
					<TableHead className="text-right">Visitas</TableHead>
					<TableHead className="text-right">Visitantes</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{items.map((item) => (
					<TableRow key={item.landing_page_path}>
						<TableCell className="font-mono text-xs">
							{item.landing_page_path}
						</TableCell>
						<TableCell className="text-right">{item.visits}</TableCell>
						<TableCell className="text-right">{item.unique_visitors}</TableCell>
					</TableRow>
				))}
			</TableBody>
		</Table>
	);
}
