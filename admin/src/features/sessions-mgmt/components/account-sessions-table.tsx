"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/ui/data-table";
import { formatDate, relativeTime } from "@/lib/format/date";
import type { AccountSession } from "../types";
import { RevokeSessionButton } from "./revoke-session-button";

/**
 * @component AccountSessionsTable
 * @description Tabla de las sesiones activas de la cuenta auth. Columnas:
 *   creada (formatDate), IP, dispositivo (user_agent), ultima actividad
 *   (relativeTime) con badge "Sesion actual" si `is_current`, y un boton
 *   Revocar por fila (deshabilitado en la sesion actual).
 *
 * @props {AccountSession[]} sessions - sesiones a renderizar
 * @props {boolean} [isLoading] - muestra skeleton rows
 */
export function AccountSessionsTable({
	sessions,
	isLoading = false,
}: {
	sessions: AccountSession[];
	isLoading?: boolean;
}) {
	const columns = useMemo<ColumnDef<AccountSession>[]>(
		() => [
			{
				accessorKey: "created_at",
				header: "Creada",
				cell: ({ row }) => formatDate(row.original.created_at),
			},
			{
				accessorKey: "ip",
				header: "IP",
				cell: ({ row }) => row.original.ip ?? "-",
			},
			{
				accessorKey: "user_agent",
				header: "Dispositivo",
				cell: ({ row }) => (
					<span
						className="block max-w-xs truncate"
						title={row.original.user_agent ?? ""}
					>
						{row.original.user_agent ?? "-"}
					</span>
				),
			},
			{
				accessorKey: "last_seen_at",
				header: "Ultima actividad",
				cell: ({ row }) => (
					<div className="flex items-center gap-2">
						<span>{relativeTime(row.original.last_seen_at)}</span>
						{row.original.is_current ? (
							<Badge variant="secondary">Sesion actual</Badge>
						) : null}
					</div>
				),
			},
			{
				id: "actions",
				header: "",
				cell: ({ row }) => (
					<div className="flex justify-end">
						<RevokeSessionButton
							sessionId={row.original.session_id}
							isCurrent={row.original.is_current}
						/>
					</div>
				),
			},
		],
		[],
	);

	return (
		<DataTable
			columns={columns}
			data={sessions}
			isLoading={isLoading}
			emptyMessage="No tienes sesiones activas"
		/>
	);
}
