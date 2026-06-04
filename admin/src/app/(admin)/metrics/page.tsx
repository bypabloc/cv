"use client";

import { useQueryClient } from "@tanstack/react-query";
import { BarChart3, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { analyticsKeys } from "@/features/analytics/api/query-keys";
import { ActiveNowBadge } from "@/features/analytics/components/ActiveNowBadge";
import { MetricsRangePicker } from "@/features/analytics/components/MetricsRangePicker";
import { OverviewKpis } from "@/features/analytics/components/OverviewKpis";
import { RetentionChart } from "@/features/analytics/components/RetentionChart";
import { TimeseriesChart } from "@/features/analytics/components/TimeseriesChart";
import { TopNichesChart } from "@/features/analytics/components/TopNichesChart";
import { TopPagesTable } from "@/features/analytics/components/TopPagesTable";
import { TopReferrersTable } from "@/features/analytics/components/TopReferrersTable";
import { useDashboard } from "@/features/analytics/hooks/use-dashboard";
import { useMetricsCloudwatchRange } from "@/features/analytics/hooks/use-metrics-cloudwatch-range";

/**
 * @page MetricsOverviewPage
 * @description Raiz del area de metricas (`/metrics`): KPIs (overview),
 *   contador (active-now), serie temporal (timeseries), rankings y retencion.
 *   Una SOLA request (`analytics/dashboard`) trae las 7 vistas. El rango
 *   from/to + bucket lo controla el selector estilo CloudWatch. SIN polling:
 *   el boton "Actualizar" invalida y recarga todas las queries de analytics.
 */
export default function MetricsOverviewPage() {
	const { range, setRange } = useMetricsCloudwatchRange();
	const dashboard = useDashboard({
		from: range.from,
		to: range.to,
		bucket: range.bucket,
	});
	const data = dashboard.data;
	const queryClient = useQueryClient();

	const refresh = () => {
		queryClient.invalidateQueries({ queryKey: analyticsKeys.all() });
	};

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<BarChart3 className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Metricas</h1>
					<ActiveNowBadge
						count={data?.active_now.active_sessions}
						standalone={false}
					/>
				</div>
				<div className="flex items-center gap-2">
					<MetricsRangePicker range={range} onChange={setRange} />
					<Button
						type="button"
						variant="outline"
						size="sm"
						className="gap-2"
						onClick={refresh}
						disabled={dashboard.isFetching}
					>
						<RefreshCw
							className={`h-4 w-4 ${dashboard.isFetching ? "animate-spin" : ""}`}
						/>
						Actualizar
					</Button>
				</div>
			</header>

			{dashboard.error ? <ErrorAlert error={dashboard.error} /> : null}

			<OverviewKpis data={data?.overview} isLoading={dashboard.isLoading} />

			<Card>
				<CardHeader>
					<CardTitle>Eventos en el tiempo</CardTitle>
				</CardHeader>
				<CardContent>
					<TimeseriesChart
						data={data?.timeseries}
						isLoading={dashboard.isLoading}
					/>
				</CardContent>
			</Card>

			<div className="grid gap-6 lg:grid-cols-2">
				<Card>
					<CardHeader>
						<CardTitle>Paginas mas vistas</CardTitle>
					</CardHeader>
					<CardContent>
						<TopPagesTable items={data?.top_pages.items ?? []} />
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Top referrers</CardTitle>
					</CardHeader>
					<CardContent>
						<TopReferrersTable
							label="Referrer"
							items={data?.top_referrers.referrers ?? []}
						/>
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Top niches</CardTitle>
					</CardHeader>
					<CardContent>
						<TopNichesChart
							data={data?.top_niches}
							isLoading={dashboard.isLoading}
						/>
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Retencion</CardTitle>
					</CardHeader>
					<CardContent>
						<RetentionChart
							data={data?.retention}
							isLoading={dashboard.isLoading}
						/>
					</CardContent>
				</Card>
			</div>
		</section>
	);
}
