"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { ActiveNowBadge } from "@/features/analytics/components/ActiveNowBadge";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { OverviewKpis } from "@/features/analytics/components/OverviewKpis";
import { RetentionChart } from "@/features/analytics/components/RetentionChart";
import { TimeseriesChart } from "@/features/analytics/components/TimeseriesChart";
import { TopNichesChart } from "@/features/analytics/components/TopNichesChart";
import { TopPagesTable } from "@/features/analytics/components/TopPagesTable";
import { TopReferrersTable } from "@/features/analytics/components/TopReferrersTable";
import { useDashboard } from "@/features/analytics/hooks/use-dashboard";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";

/**
 * @page MetricsOverviewPage
 * @description Raiz del area de metricas (`/metrics`): KPIs (overview),
 *   contador live (active-now), serie temporal (timeseries), rankings y
 *   retencion. Una SOLA request (`analytics/dashboard`) trae las 7 vistas en
 *   vez de 7 requests separadas; el rango from/to es compartido por la page.
 */
export default function MetricsOverviewPage() {
	const { range, setRange } = useMetricsRange();
	const dashboard = useDashboard({ ...range, bucket: "day" });
	const data = dashboard.data;

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
				<MetricsDateRange range={range} onChange={setRange} />
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
