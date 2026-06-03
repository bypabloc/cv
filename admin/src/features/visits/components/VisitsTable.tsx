"use client";

import { Badge } from "@/components/ui/badge";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import { formatDate } from "@/lib/format/date";
import type { VisitRow } from "../types";

/**
 * @component VisitsTable
 * @description Tabla del listado de visitas (visits/list): started_at, country,
 *   niche, referrer, landing_page_path, event_count. Vacio muestra un mensaje.
 *
 * @props {VisitRow[]} items - filas de visitas
 */
export function VisitsTable({ items }: { items: VisitRow[] }) {
	if (items.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin visitas en el rango seleccionado.
			</p>
		);
	}
	return (
		<Table>
			<TableHeader>
				<TableRow>
					<TableHead>Inicio</TableHead>
					<TableHead>Pais</TableHead>
					<TableHead>Niche</TableHead>
					<TableHead>Referrer</TableHead>
					<TableHead>Landing</TableHead>
					<TableHead className="text-right">Eventos</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{items.map((item) => (
					<TableRow key={item.visit_id}>
						<TableCell className="whitespace-nowrap">
							{formatDate(item.started_at)}
						</TableCell>
						<TableCell>{item.country ?? "-"}</TableCell>
						<TableCell>
							{item.niche ? (
								<Badge variant="secondary">{item.niche}</Badge>
							) : (
								"-"
							)}
						</TableCell>
						<TableCell className="max-w-[16rem] truncate text-xs text-muted-foreground">
							{item.referrer ?? "-"}
						</TableCell>
						<TableCell className="max-w-[16rem] truncate font-mono text-xs">
							{item.landing_page_path ?? "-"}
						</TableCell>
						<TableCell className="text-right">{item.event_count}</TableCell>
					</TableRow>
				))}
			</TableBody>
		</Table>
	);
}
