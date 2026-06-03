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
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { useOverview } from "@/features/analytics/hooks/use-overview";
import { useRetention } from "@/features/analytics/hooks/use-retention";
import { useTimeseries } from "@/features/analytics/hooks/use-timeseries";
import { useTopNiches } from "@/features/analytics/hooks/use-top-niches";
import { useTopPages } from "@/features/analytics/hooks/use-top-pages";
import { useTopReferrers } from "@/features/analytics/hooks/use-top-referrers";

/**
 * @page MetricsOverviewPage
 * @description Raiz del area de metricas (`/metrics`): KPIs (overview),
 *   contador live (active-now), serie temporal (timeseries) y ranking de
 *   paginas (top-pages). El rango from/to es compartido por la page.
 */
export default function MetricsOverviewPage() {
	const { range, setRange } = useMetricsRange();
	const overview = useOverview(range);
	const timeseries = useTimeseries({ ...range, bucket: "day" });
	const topPages = useTopPages(range);
	const topReferrers = useTopReferrers(range);
	const topNiches = useTopNiches(range);
	const retention = useRetention(range);

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<BarChart3 className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Metricas</h1>
					<ActiveNowBadge />
				</div>
				<MetricsDateRange range={range} onChange={setRange} />
			</header>

			{overview.error ? <ErrorAlert error={overview.error} /> : null}

			<OverviewKpis data={overview.data} isLoading={overview.isLoading} />

			<Card>
				<CardHeader>
					<CardTitle>Eventos en el tiempo</CardTitle>
				</CardHeader>
				<CardContent>
					<TimeseriesChart
						data={timeseries.data}
						isLoading={timeseries.isLoading}
					/>
				</CardContent>
			</Card>

			<div className="grid gap-6 lg:grid-cols-2">
				<Card>
					<CardHeader>
						<CardTitle>Paginas mas vistas</CardTitle>
					</CardHeader>
					<CardContent>
						{topPages.error ? (
							<ErrorAlert error={topPages.error} />
						) : (
							<TopPagesTable items={topPages.data?.items ?? []} />
						)}
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Top referrers</CardTitle>
					</CardHeader>
					<CardContent>
						{topReferrers.error ? (
							<ErrorAlert error={topReferrers.error} />
						) : (
							<TopReferrersTable
								label="Referrer"
								items={topReferrers.data?.referrers ?? []}
							/>
						)}
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Top niches</CardTitle>
					</CardHeader>
					<CardContent>
						{topNiches.error ? (
							<ErrorAlert error={topNiches.error} />
						) : (
							<TopNichesChart
								data={topNiches.data}
								isLoading={topNiches.isLoading}
							/>
						)}
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Retencion</CardTitle>
					</CardHeader>
					<CardContent>
						{retention.error ? (
							<ErrorAlert error={retention.error} />
						) : (
							<RetentionChart
								data={retention.data}
								isLoading={retention.isLoading}
							/>
						)}
					</CardContent>
				</Card>
			</div>
		</section>
	);
}
