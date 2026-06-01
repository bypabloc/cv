"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import { DataTable } from "@/components/ui/data-table";
import { formatDate } from "@/lib/format/date";
import type { AdminUser } from "@/types/models";
import { StatusBadge } from "./status-badge";
import { UserActionsMenu } from "./user-actions-menu";

/**
 * @component UsersTable
 * @description DataTable de usuarios (admin.list-users). Columnas: email,
 *   display_name, badge de status, total_mfa, created_at (formateado) y un menu
 *   de acciones por fila. El click en una fila abre el detalle via
 *   `onSelectUser(user_id)` (la page lo traduce a `?user=<id>`).
 * @props {AdminUser[]} users - filas
 * @props {boolean} [isLoading] - estado de carga
 * @props {(userId: string) => void} onSelectUser - abre el detalle del usuario
 */
export function UsersTable({
	users,
	isLoading = false,
	onSelectUser,
}: {
	users: AdminUser[];
	isLoading?: boolean;
	onSelectUser: (userId: string) => void;
}) {
	const columns = useMemo<ColumnDef<AdminUser>[]>(
		() => [
			{
				accessorKey: "email",
				header: "Email",
			},
			{
				accessorKey: "display_name",
				header: "Nombre",
				cell: ({ row }) => row.original.display_name ?? "-",
			},
			{
				accessorKey: "status",
				header: "Estado",
				cell: ({ row }) => <StatusBadge status={row.original.status} />,
			},
			{
				accessorKey: "total_mfa",
				header: "MFA",
			},
			{
				accessorKey: "created_at",
				header: "Creado",
				cell: ({ row }) => formatDate(row.original.created_at),
			},
			{
				id: "actions",
				header: "",
				// El menu detiene la propagacion del click en su propio trigger para
				// no abrir el detalle de la fila (ver UserActionsMenu).
				cell: ({ row }) => <UserActionsMenu user={row.original} />,
			},
		],
		[],
	);

	return (
		<DataTable
			columns={columns}
			data={users}
			isLoading={isLoading}
			emptyMessage="No hay usuarios"
			onRowClick={(row) => onSelectUser(row.user_id)}
		/>
	);
}
