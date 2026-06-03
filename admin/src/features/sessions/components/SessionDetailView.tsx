"use client";

import { ArrowLeft, SearchX } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Skeleton } from "@/components/ui/skeleton";
import { SessionVisitsTable } from "@/features/sessions/components/SessionVisitsTable";
import { useSessionDetail } from "@/features/sessions/hooks/use-session-detail";
import { ApiError } from "@/lib/api-client";
import { formatDate } from "@/lib/format/date";
import { ROUTES } from "@/lib/routes";

/**
 * @component SessionDetailView
 * @description Detalle de una sesion de visitante (sessions/detail): resumen de
 *   la sesion + total de eventos + tabla de visitas. Recibe el `sessionId` como
 *   prop (la page lo lee del path con useParams). Un 404 del backend (sesion
 *   inexistente) muestra un EmptyState.
 *
 * @props {string} sessionId - id de la sesion a mostrar
 */
export function SessionDetailView({ sessionId }: { sessionId: string }) {
	const detail = useSessionDetail({ session_id: sessionId });

	const isNotFound =
		detail.error instanceof ApiError && detail.error.status === 404;

	return (
		<section className="space-y-6">
			<header className="flex items-center gap-3">
				<Button variant="ghost" size="sm" asChild>
					<Link href={ROUTES.admin.metricsSessions}>
						<ArrowLeft className="h-4 w-4" />
						Volver
					</Link>
				</Button>
				<h1 className="font-mono text-lg font-semibold">{sessionId}</h1>
			</header>

			{isNotFound ? (
				<EmptyState
					icon={SearchX}
					title="Sesion no encontrada"
					description="La sesion solicitada no existe o esta fuera del periodo de retencion."
					action={
						<Button variant="outline" asChild>
							<Link href={ROUTES.admin.metricsSessions}>
								Ver todas las sesiones
							</Link>
						</Button>
					}
				/>
			) : detail.error ? (
				<ErrorAlert error={detail.error} onRetry={() => detail.refetch()} />
			) : (
				<>
					<div className="grid gap-4 md:grid-cols-3">
						<Card>
							<CardHeader className="pb-2">
								<CardTitle className="text-sm font-medium text-muted-foreground">
									Visitas
								</CardTitle>
							</CardHeader>
							<CardContent>
								{detail.isLoading || !detail.data ? (
									<Skeleton className="h-7 w-16" />
								) : (
									<p className="text-2xl font-semibold">
										{detail.data.session.visits_count}
									</p>
								)}
							</CardContent>
						</Card>
						<Card>
							<CardHeader className="pb-2">
								<CardTitle className="text-sm font-medium text-muted-foreground">
									Eventos
								</CardTitle>
							</CardHeader>
							<CardContent>
								{detail.isLoading || !detail.data ? (
									<Skeleton className="h-7 w-16" />
								) : (
									<p className="text-2xl font-semibold">
										{detail.data.events_count}
									</p>
								)}
							</CardContent>
						</Card>
						<Card>
							<CardHeader className="pb-2">
								<CardTitle className="text-sm font-medium text-muted-foreground">
									Dispositivo
								</CardTitle>
							</CardHeader>
							<CardContent>
								{detail.isLoading || !detail.data ? (
									<Skeleton className="h-7 w-24" />
								) : (
									<Badge variant="secondary">
										{detail.data.session.device_type}
									</Badge>
								)}
							</CardContent>
						</Card>
					</div>

					<Card>
						<CardHeader>
							<CardTitle>Resumen de la sesion</CardTitle>
						</CardHeader>
						<CardContent>
							{detail.isLoading || !detail.data ? (
								<div className="grid gap-3 sm:grid-cols-2">
									{["f1", "f2", "f3", "f4"].map((fieldKey) => (
										<Skeleton key={fieldKey} className="h-5 w-full" />
									))}
								</div>
							) : (
								<dl className="grid gap-3 text-sm sm:grid-cols-2">
									<div>
										<dt className="text-muted-foreground">Navegador</dt>
										<dd>
											{detail.data.session.browser}{" "}
											{detail.data.session.browser_version}
										</dd>
									</div>
									<div>
										<dt className="text-muted-foreground">Sistema operativo</dt>
										<dd>{detail.data.session.os}</dd>
									</div>
									<div>
										<dt className="text-muted-foreground">Primera vez</dt>
										<dd>{formatDate(detail.data.session.first_seen_at)}</dd>
									</div>
									<div>
										<dt className="text-muted-foreground">Ultima vez</dt>
										<dd>{formatDate(detail.data.session.last_seen_at)}</dd>
									</div>
								</dl>
							)}
						</CardContent>
					</Card>

					<Card>
						<CardHeader>
							<CardTitle>Visitas</CardTitle>
						</CardHeader>
						<CardContent>
							{detail.isLoading || !detail.data ? (
								<Skeleton className="h-40 w-full" />
							) : (
								<SessionVisitsTable visits={detail.data.visits} />
							)}
						</CardContent>
					</Card>
				</>
			)}
		</section>
	);
}
