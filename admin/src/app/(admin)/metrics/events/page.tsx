"use client";

import { MousePointerClick } from "lucide-react";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { EventDistributionChart } from "@/features/events/components/EventDistributionChart";
import { EventDistributionTable } from "@/features/events/components/EventDistributionTable";
import { EventHeatmap } from "@/features/events/components/EventHeatmap";
import { EventListTable } from "@/features/events/components/EventListTable";
import { useDistribution } from "@/features/events/hooks/use-distribution";
import { useEventList } from "@/features/events/hooks/use-event-list";
import { useHeatmap } from "@/features/events/hooks/use-heatmap";

const PAGE_SIZE = 50;

/**
 * @page MetricsEventsPage
 * @description Area de eventos (`/metrics/events`) con tres tabs: la
 *   distribucion de tipos de evento (events/distribution, chart + tabla), el
 *   listado crudo paginado (events/list) y el heatmap dia x hora
 *   (events/heatmap). El rango from/to es compartido por la page.
 */
export default function MetricsEventsPage() {
	const { range, setRange } = useMetricsRange();
	const [page, setPage] = useState(1);

	const distribution = useDistribution(range);
	const list = useEventList({ ...range, page, page_size: PAGE_SIZE });
	const heatmap = useHeatmap(range);

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<MousePointerClick className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Eventos</h1>
				</div>
				<MetricsDateRange
					range={range}
					onChange={(next) => {
						setPage(1);
						setRange(next);
					}}
				/>
			</header>

			<Tabs defaultValue="distribution">
				<TabsList>
					<TabsTrigger value="distribution">Distribucion</TabsTrigger>
					<TabsTrigger value="list">Listado</TabsTrigger>
					<TabsTrigger value="heatmap">Heatmap</TabsTrigger>
				</TabsList>

				<TabsContent value="distribution">
					<Card>
						<CardHeader>
							<CardTitle>Distribucion por tipo de evento</CardTitle>
						</CardHeader>
						<CardContent className="space-y-6">
							{distribution.error ? (
								<ErrorAlert error={distribution.error} />
							) : (
								<>
									<EventDistributionChart
										data={distribution.data}
										isLoading={distribution.isLoading}
									/>
									{!distribution.isLoading && distribution.data ? (
										<EventDistributionTable items={distribution.data.items} />
									) : null}
								</>
							)}
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="list">
					<Card>
						<CardHeader>
							<CardTitle>Listado de eventos</CardTitle>
						</CardHeader>
						<CardContent>
							{list.error ? (
								<ErrorAlert error={list.error} />
							) : (
								<EventListTable
									data={list.data}
									isLoading={list.isLoading}
									page={page}
									onPageChange={setPage}
								/>
							)}
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="heatmap">
					<Card>
						<CardHeader>
							<CardTitle>Eventos por dia y hora</CardTitle>
						</CardHeader>
						<CardContent>
							{heatmap.error ? (
								<ErrorAlert error={heatmap.error} />
							) : (
								<EventHeatmap
									data={heatmap.data}
									isLoading={heatmap.isLoading}
								/>
							)}
						</CardContent>
					</Card>
				</TabsContent>
			</Tabs>
		</section>
	);
}
