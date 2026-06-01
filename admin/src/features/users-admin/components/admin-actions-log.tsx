"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import { DataTable } from "@/components/ui/data-table";
import { ErrorAlert } from "@/components/ui/error-alert";
import { formatDate } from "@/lib/format/date";
import type { AdminAction } from "@/types/models";
import { useAdminActions } from "../hooks/use-admin-actions";

/**
 * @component AdminActionsLog
 * @description DataTable del log de acciones administrativas
 *   (admin.list-admin-actions). Columnas: actor, target, action y created_at
 *   (formateado). Maneja loading + error internamente.
 */
export function AdminActionsLog() {
	const { data: actions, isLoading, error, refetch } = useAdminActions();

	const columns = useMemo<ColumnDef<AdminAction>[]>(
		() => [
			{
				accessorKey: "actor_user_id",
				header: "Actor",
			},
			{
				accessorKey: "target_user_id",
				header: "Objetivo",
				cell: ({ row }) => row.original.target_user_id ?? "-",
			},
			{
				accessorKey: "action",
				header: "Accion",
			},
			{
				accessorKey: "created_at",
				header: "Fecha",
				cell: ({ row }) => formatDate(row.original.created_at),
			},
		],
		[],
	);

	if (error) {
		return <ErrorAlert error={error} onRetry={() => refetch()} />;
	}

	return (
		<DataTable
			columns={columns}
			data={actions ?? []}
			isLoading={isLoading}
			emptyMessage="Sin acciones registradas"
		/>
	);
}
