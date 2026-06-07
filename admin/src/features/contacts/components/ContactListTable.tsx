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
import type { ContactListResponse } from "../types";
import { ContactStatusBadge } from "./ContactStatusBadge";

const SKELETON_ROWS = ["sk1", "sk2", "sk3", "sk4", "sk5"] as const;
const SKELETON_CELLS = ["c1", "c2", "c3", "c4", "c5", "c6"] as const;

/**
 * @component ContactListTable
 * @description Listado crudo paginado de contactos (contacts/list). Columnas:
 *   created_at, name, email, status (Badge), niche, company. Pagina con
 *   botones anterior/siguiente sobre el estado `page` (controlado por la
 *   page). Muestra `total` y `has_more`. Skeleton mientras carga.
 *
 * @props {ContactListResponse} [data] - pagina de contactos del backend
 * @props {boolean} isLoading - estado de carga
 * @props {number} page - pagina actual (1-based)
 * @props {(page: number) => void} onPageChange - cambia de pagina
 */
export function ContactListTable({
	data,
	isLoading,
	page,
	onPageChange,
}: {
	data?: ContactListResponse;
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
							<TableHead>Nombre</TableHead>
							<TableHead>Email</TableHead>
							<TableHead>Estado</TableHead>
							<TableHead>Niche</TableHead>
							<TableHead>Empresa</TableHead>
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
									Sin contactos en el rango seleccionado.
								</TableCell>
							</TableRow>
						) : (
							items.map((row) => (
								<TableRow key={row.id}>
									<TableCell className="whitespace-nowrap text-xs">
										{formatDate(row.created_at)}
									</TableCell>
									<TableCell className="font-medium">{row.name}</TableCell>
									<TableCell className="font-mono text-xs">
										{row.email}
									</TableCell>
									<TableCell>
										<ContactStatusBadge status={row.status} />
									</TableCell>
									<TableCell>
										<Badge variant="secondary">{row.niche}</Badge>
									</TableCell>
									<TableCell className="text-muted-foreground">
										{row.company ?? "-"}
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
					{total > 0 ? ` · ${total} contactos en total` : ""}
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
