"use client";

import { Monitor } from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Skeleton } from "@/components/ui/skeleton";
import { AccountSessionsTable } from "@/features/sessions-mgmt/components/account-sessions-table";
import { useAccountSessions } from "@/features/sessions-mgmt/hooks/use-account-sessions";
import { useAccountStatus } from "@/features/sessions-mgmt/hooks/use-account-status";

/**
 * @page SettingsSessionsPage
 * @description Tab "Sesiones" de /settings (los tabs viven en el layout).
 *   Sesiones activas de MI cuenta auth (logins en otros dispositivos) +
 *   estado de la cuenta. Puedes revocar cualquiera salvo la actual. NO es el
 *   tracking de visitantes (eso vive en /metrics).
 */
export default function SettingsSessionsPage() {
	const status = useAccountStatus();
	const sessions = useAccountSessions();

	return (
		<div className="space-y-6">
			<p className="text-sm text-muted-foreground">
				Dispositivos donde tu cuenta tiene una sesion activa. Puedes revocar
				cualquiera salvo la actual.
			</p>

			<Card>
				<CardHeader>
					<CardTitle>Estado de la cuenta</CardTitle>
					<CardDescription>
						Informacion de tu cuenta y la sesion en curso.
					</CardDescription>
				</CardHeader>
				<CardContent>
					{status.isPending ? (
						<Skeleton className="h-12 w-full" />
					) : status.isError ? (
						<ErrorAlert error={status.error} onRetry={() => status.refetch()} />
					) : (
						<dl className="grid gap-2 text-sm sm:grid-cols-3">
							<div>
								<dt className="text-muted-foreground">Usuario</dt>
								<dd className="font-mono break-all">{status.data.user_id}</dd>
							</div>
							<div>
								<dt className="text-muted-foreground">Estado</dt>
								<dd>{status.data.status}</dd>
							</div>
							<div>
								<dt className="text-muted-foreground">Sesion actual</dt>
								<dd className="font-mono break-all">
									{status.data.current_session_id ?? "-"}
								</dd>
							</div>
						</dl>
					)}
				</CardContent>
			</Card>

			{sessions.isError ? (
				<ErrorAlert error={sessions.error} onRetry={() => sessions.refetch()} />
			) : !sessions.isPending && sessions.data.length === 0 ? (
				<EmptyState
					icon={Monitor}
					title="No tienes sesiones activas"
					description="Cuando inicies sesion en otros dispositivos apareceran aqui."
				/>
			) : (
				<AccountSessionsTable
					sessions={sessions.data ?? []}
					isLoading={sessions.isPending}
				/>
			)}
		</div>
	);
}
