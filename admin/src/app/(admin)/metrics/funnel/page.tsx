"use client";

import { Filter } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { FunnelChart } from "@/features/funnel/components/FunnelChart";
import { useConversion } from "@/features/funnel/hooks/use-conversion";

/**
 * @page FunnelPage
 * @description Embudo de conversion (`/metrics/funnel`): session -> visit ->
 *   contact con sus tasas (funnel/conversion). El rango from/to es compartido
 *   con el resto de las pages de metricas.
 */
export default function FunnelPage() {
	const { range, setRange } = useMetricsRange();
	const conversion = useConversion(range);

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<Filter className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Embudo de conversion</h1>
				</div>
				<MetricsDateRange range={range} onChange={setRange} />
			</header>

			{conversion.error ? <ErrorAlert error={conversion.error} /> : null}

			<Card>
				<CardHeader>
					<CardTitle>Sesiones a contactos</CardTitle>
				</CardHeader>
				<CardContent>
					<FunnelChart
						data={conversion.data}
						isLoading={conversion.isLoading}
					/>
				</CardContent>
			</Card>
		</section>
	);
}
