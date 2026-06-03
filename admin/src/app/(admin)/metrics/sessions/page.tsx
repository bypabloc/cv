"use client";

import { Users } from "lucide-react";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { SessionFilters } from "@/features/sessions/components/SessionFilters";
import { SessionsPagination } from "@/features/sessions/components/SessionsPagination";
import { SessionsTable } from "@/features/sessions/components/SessionsTable";
import { useSessionList } from "@/features/sessions/hooks/use-session-list";

const PAGE_SIZE = 25;

/**
 * @page MetricsSessionsPage
 * @description Listado paginado de sesiones de visitantes (sessions/list).
 *   Comparte el rango from/to con el resto del area de metricas. Filtros
 *   opcionales por device_type y browser; al cambiar un filtro o el rango se
 *   vuelve a la pagina 1.
 */
export default function MetricsSessionsPage() {
	const { range, setRange } = useMetricsRange();
	const [page, setPage] = useState(1);
	const [deviceType, setDeviceType] = useState<string | undefined>();
	const [browser, setBrowser] = useState<string | undefined>();

	const sessions = useSessionList({
		...range,
		page,
		page_size: PAGE_SIZE,
		device_type: deviceType,
		browser,
	});

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<Users className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Sesiones</h1>
				</div>
				<MetricsDateRange
					range={range}
					onChange={(next) => {
						setPage(1);
						setRange(next);
					}}
				/>
			</header>

			<Card>
				<CardHeader>
					<CardTitle>Sesiones de visitantes</CardTitle>
				</CardHeader>
				<CardContent className="space-y-4">
					<SessionFilters
						deviceType={deviceType}
						browser={browser}
						onDeviceTypeChange={(value) => {
							setPage(1);
							setDeviceType(value);
						}}
						onBrowserChange={(value) => {
							setPage(1);
							setBrowser(value);
						}}
					/>

					{sessions.error ? (
						<ErrorAlert
							error={sessions.error}
							onRetry={() => sessions.refetch()}
						/>
					) : (
						<>
							<SessionsTable
								items={sessions.data?.items ?? []}
								isLoading={sessions.isLoading}
							/>
							<SessionsPagination
								page={sessions.data?.page ?? page}
								pageSize={sessions.data?.page_size ?? PAGE_SIZE}
								total={sessions.data?.total ?? 0}
								hasMore={sessions.data?.has_more ?? false}
								isLoading={sessions.isLoading || sessions.isFetching}
								onPageChange={setPage}
							/>
						</>
					)}
				</CardContent>
			</Card>
		</section>
	);
}
