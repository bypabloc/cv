"use client";

import { ShieldOff, Users } from "lucide-react";
import { useRouter } from "next/navigation";
import { Suspense, useCallback } from "react";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdminActionsLog } from "@/features/users-admin/components/admin-actions-log";
import { UserDetailDrawer } from "@/features/users-admin/components/user-detail-drawer";
import { UsersTable } from "@/features/users-admin/components/users-table";
import { useUsersList } from "@/features/users-admin/hooks/use-users-list";
import { ApiError } from "@/lib/api-client";
import { ROUTES } from "@/lib/routes";

/**
 * @page UsersAdminPage
 * @description Gestion de OTROS usuarios (solo admin). Lista + detalle (deep-link
 *   `?user=<id>` en un Sheet, dentro de Suspense) + log de acciones admin. Si el
 *   backend responde 404 (caller no admin), muestra un EmptyState de acceso
 *   denegado SIN filtrar la existencia del recurso (anti-enumeration).
 */
export default function UsersAdminPage() {
	const router = useRouter();
	const { data, isLoading, error } = useUsersList();

	const handleSelectUser = useCallback(
		(userId: string) => {
			router.replace(
				`${ROUTES.admin.users}?user=${encodeURIComponent(userId)}`,
			);
		},
		[router],
	);

	// Gate anti-enumeration: 404 -> el caller no es admin. No se filtra el recurso.
	if (error instanceof ApiError && error.status === 404) {
		return (
			<EmptyState
				icon={ShieldOff}
				title="No tienes acceso a esta seccion"
				description="La gestion de usuarios esta disponible solo para administradores."
			/>
		);
	}

	return (
		<section className="space-y-6">
			<header className="flex items-center gap-3">
				<Users className="h-5 w-5 text-muted-foreground" />
				<h1 className="text-2xl font-semibold">Usuarios</h1>
			</header>

			<Tabs defaultValue="users">
				<TabsList>
					<TabsTrigger value="users">Usuarios</TabsTrigger>
					<TabsTrigger value="actions">Acciones admin</TabsTrigger>
				</TabsList>

				<TabsContent value="users" className="space-y-4">
					{error ? (
						<ErrorAlert error={error} />
					) : (
						<UsersTable
							users={data?.users ?? []}
							isLoading={isLoading}
							onSelectUser={handleSelectUser}
						/>
					)}
				</TabsContent>

				<TabsContent value="actions">
					<AdminActionsLog />
				</TabsContent>
			</Tabs>

			<Suspense fallback={null}>
				<UserDetailDrawer />
			</Suspense>
		</section>
	);
}
