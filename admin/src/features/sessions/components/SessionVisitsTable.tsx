"use client";

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
 * @component SessionVisitsTable
 * @description Tabla de visitas de una sesion (sessions/detail.visits).
 *   Columnas: started_at, landing_page_path, niche, referrer, country,
 *   utm_source/medium/campaign y event_count.
 *
 * @props {VisitRow[]} visits - filas de visitas de la sesion
 */
export function SessionVisitsTable({ visits }: { visits: VisitRow[] }) {
	if (visits.length === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Esta sesion no tiene visitas registradas.
			</p>
		);
	}
	return (
		<div className="rounded-md border">
			<Table>
				<TableHeader>
					<TableRow>
						<TableHead>Inicio</TableHead>
						<TableHead>Landing</TableHead>
						<TableHead>Niche</TableHead>
						<TableHead>Referrer</TableHead>
						<TableHead>Pais</TableHead>
						<TableHead>UTM</TableHead>
						<TableHead className="text-right">Eventos</TableHead>
					</TableRow>
				</TableHeader>
				<TableBody>
					{visits.map((visit) => {
						const utm = [visit.utm_source, visit.utm_medium, visit.utm_campaign]
							.filter(Boolean)
							.join(" / ");
						return (
							<TableRow key={visit.visit_id}>
								<TableCell className="text-muted-foreground">
									{formatDate(visit.started_at)}
								</TableCell>
								<TableCell className="font-mono text-xs">
									{visit.landing_page_path || "-"}
								</TableCell>
								<TableCell>{visit.niche || "-"}</TableCell>
								<TableCell className="max-w-48 truncate text-xs text-muted-foreground">
									{visit.referrer || "-"}
								</TableCell>
								<TableCell>{visit.country || "-"}</TableCell>
								<TableCell className="text-xs text-muted-foreground">
									{utm || "-"}
								</TableCell>
								<TableCell className="text-right">
									{visit.event_count}
								</TableCell>
							</TableRow>
						);
					})}
				</TableBody>
			</Table>
		</div>
	);
}
