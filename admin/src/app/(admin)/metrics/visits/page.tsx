"use client";

import { Eye } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { LandingPagesTable } from "@/features/visits/components/LandingPagesTable";
import { VisitsTable } from "@/features/visits/components/VisitsTable";
import { useLandingPages } from "@/features/visits/hooks/use-landing-pages";
import { useVisitsList } from "@/features/visits/hooks/use-visits-list";

const PAGE_SIZE = 20;

/**
 * @page MetricsVisitsPage
 * @description Area de visitas (`/metrics/visits`) con dos tabs: el listado
 *   paginado de visitas (visits/list) y el ranking de landing pages
 *   (visits/landing-pages). El rango from/to es compartido por la page.
 */
export default function MetricsVisitsPage() {
	const { range, setRange } = useMetricsRange();
	const [page, setPage] = useState(1);

	const list = useVisitsList({ ...range, page, page_size: PAGE_SIZE });
	const landingPages = useLandingPages(range);

	const total = list.data?.total ?? 0;
	const hasMore = list.data?.has_more ?? false;

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<Eye className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Visitas</h1>
				</div>
				<MetricsDateRange
					range={range}
					onChange={(next) => {
						setPage(1);
						setRange(next);
					}}
				/>
			</header>

			<Tabs defaultValue="list">
				<TabsList>
					<TabsTrigger value="list">Listado</TabsTrigger>
					<TabsTrigger value="landing">Landing pages</TabsTrigger>
				</TabsList>

				<TabsContent value="list">
					<Card>
						<CardHeader>
							<CardTitle>Listado de visitas</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							{list.error ? (
								<ErrorAlert error={list.error} />
							) : list.isLoading ? (
								<Skeleton className="h-72 w-full" />
							) : (
								<>
									<VisitsTable items={list.data?.items ?? []} />
									<div className="flex items-center justify-between">
										<p className="text-sm text-muted-foreground">
											Pagina {page} · {total} visitas
										</p>
										<div className="flex gap-2">
											<Button
												variant="outline"
												size="sm"
												disabled={page <= 1}
												onClick={() => setPage((p) => Math.max(1, p - 1))}
											>
												Anterior
											</Button>
											<Button
												variant="outline"
												size="sm"
												disabled={!hasMore}
												onClick={() => setPage((p) => p + 1)}
											>
												Cargar mas
											</Button>
										</div>
									</div>
								</>
							)}
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="landing">
					<Card>
						<CardHeader>
							<CardTitle>Landing pages</CardTitle>
						</CardHeader>
						<CardContent>
							{landingPages.error ? (
								<ErrorAlert error={landingPages.error} />
							) : landingPages.isLoading ? (
								<Skeleton className="h-72 w-full" />
							) : (
								<LandingPagesTable items={landingPages.data?.items ?? []} />
							)}
						</CardContent>
					</Card>
				</TabsContent>
			</Tabs>
		</section>
	);
}
