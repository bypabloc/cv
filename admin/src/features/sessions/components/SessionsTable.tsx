"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import { formatDate } from "@/lib/format/date";
import { ROUTES } from "@/lib/routes";
import type { SessionRow } from "../types";

const SKELETON_ROWS = ["sk1", "sk2", "sk3", "sk4", "sk5"] as const;
const SKELETON_CELLS = ["c1", "c2", "c3", "c4", "c5", "c6"] as const;

/**
 * @component SessionsTable
 * @description Tabla del listado de sesiones de visitantes (sessions/list).
 *   Columnas: session_id (mono, link al detalle), browser, os, device_type
 *   (badge), visits_count, last_seen_at (formateado). Muestra skeleton rows
 *   mientras carga y un mensaje cuando no hay filas.
 *
 * @props {SessionRow[]} items - filas de sesiones
 * @props {boolean} isLoading - estado de carga
 */
export function SessionsTable({
	items,
	isLoading,
}: {
	items: SessionRow[];
	isLoading: boolean;
}) {
	return (
		<div className="rounded-md border">
			<Table>
				<TableHeader>
					<TableRow>
						<TableHead>Sesion</TableHead>
						<TableHead>Navegador</TableHead>
						<TableHead>SO</TableHead>
						<TableHead>Dispositivo</TableHead>
						<TableHead className="text-right">Visitas</TableHead>
						<TableHead>Ultima vez</TableHead>
					</TableRow>
				</TableHeader>
				<TableBody>
					{isLoading ? (
						SKELETON_ROWS.map((rowKey) => (
							<TableRow key={rowKey}>
								{SKELETON_CELLS.map((cellKey) => (
									<TableCell key={`${rowKey}-${cellKey}`}>
										<Skeleton className="h-5 w-full" />
									</TableCell>
								))}
							</TableRow>
						))
					) : items.length === 0 ? (
						<TableRow>
							<TableCell
								colSpan={6}
								className="h-24 text-center text-muted-foreground"
							>
								Sin sesiones en el rango seleccionado.
							</TableCell>
						</TableRow>
					) : (
						items.map((row) => (
							<TableRow key={row.session_id}>
								<TableCell className="font-mono text-xs">
									<Link
										href={ROUTES.admin.metricsSessionDetail(row.session_id)}
										className="text-primary hover:underline"
									>
										{row.session_id}
									</Link>
								</TableCell>
								<TableCell>
									{row.browser}
									{row.browser_version ? (
										<span className="text-muted-foreground">
											{" "}
											{row.browser_version}
										</span>
									) : null}
								</TableCell>
								<TableCell>{row.os}</TableCell>
								<TableCell>
									<Badge variant="secondary">{row.device_type}</Badge>
								</TableCell>
								<TableCell className="text-right">{row.visits_count}</TableCell>
								<TableCell className="text-muted-foreground">
									{formatDate(row.last_seen_at)}
								</TableCell>
							</TableRow>
						))
					)}
				</TableBody>
			</Table>
		</div>
	);
}
