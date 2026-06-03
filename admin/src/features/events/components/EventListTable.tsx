"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import type { EventListResponse } from "../types";

const SKELETON_ROWS = ["sk1", "sk2", "sk3", "sk4", "sk5"] as const;
const SKELETON_CELLS = ["c1", "c2", "c3", "c4", "c5"] as const;

/**
 * @component EventListTable
 * @description Listado crudo paginado de eventos (events/list). Columnas:
 *   created_at, event_type, page_path, niche, session_id. Pagina con botones
 *   anterior/siguiente sobre el estado `page` (controlado por la page). Muestra
 *   `total` y `has_more`. Skeleton mientras carga.
 *
 * @props {EventListResponse} [data] - pagina de eventos del backend
 * @props {boolean} isLoading - estado de carga
 * @props {number} page - pagina actual (1-based)
 * @props {(page: number) => void} onPageChange - cambia de pagina
 */
export function EventListTable({
	data,
	isLoading,
	page,
	onPageChange,
}: {
	data?: EventListResponse;
	isLoading: boolean;
	page: number;
	onPageChange: (page: number) => void;
}) {
	const items = data?.items ?? [];
	const hasMore = data?.has_more ?? false;
	const total = data?.total ?? 0;

	return (
		<div className="space-y-4">
			<div className="rounded-md border">
				<Table>
					<TableHeader>
						<TableRow>
							<TableHead>Fecha</TableHead>
							<TableHead>Tipo</TableHead>
							<TableHead>Pagina</TableHead>
							<TableHead>Niche</TableHead>
							<TableHead>Sesion</TableHead>
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
									colSpan={5}
									className="h-24 text-center text-muted-foreground"
								>
									Sin eventos en el rango seleccionado.
								</TableCell>
							</TableRow>
						) : (
							items.map((row) => (
								<TableRow key={`${row.visit_id}-${row.created_at}`}>
									<TableCell className="whitespace-nowrap text-xs">
										{formatDate(row.created_at)}
									</TableCell>
									<TableCell className="font-mono text-xs">
										{row.event_type}
									</TableCell>
									<TableCell className="font-mono text-xs">
										{row.page_path}
									</TableCell>
									<TableCell>
										<Badge variant="secondary">{row.niche}</Badge>
									</TableCell>
									<TableCell className="font-mono text-xs text-muted-foreground">
										{row.session_id}
									</TableCell>
								</TableRow>
							))
						)}
					</TableBody>
				</Table>
			</div>

			<div className="flex items-center justify-between">
				<p className="text-sm text-muted-foreground">
					Pagina {page}
					{total > 0 ? ` · ${total} eventos en total` : ""}
				</p>
				<div className="flex gap-2">
					<Button
						variant="outline"
						size="sm"
						disabled={page <= 1 || isLoading}
						onClick={() => onPageChange(page - 1)}
					>
						Anterior
					</Button>
					<Button
						variant="outline"
						size="sm"
						disabled={!hasMore || isLoading}
						onClick={() => onPageChange(page + 1)}
					>
						Siguiente
					</Button>
				</div>
			</div>
		</div>
	);
}
