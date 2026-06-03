"use client";

import { Globe } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { GeoCountryChart } from "@/features/geo/components/GeoCountryChart";
import { GeoCountryTable } from "@/features/geo/components/GeoCountryTable";
import { useByCountry } from "@/features/geo/hooks/use-by-country";

/**
 * @page MetricsGeoPage
 * @description Metricas geograficas (`/metrics/geo`): ranking de paises por
 *   sesiones (geo/by-country). Grafico con el top 10 + tabla completa. El rango
 *   from/to es compartido (useMetricsRange).
 */
export default function MetricsGeoPage() {
	const { range, setRange } = useMetricsRange();
	const byCountry = useByCountry(range);

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<Globe className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Geografia</h1>
				</div>
				<MetricsDateRange range={range} onChange={setRange} />
			</header>

			{byCountry.error ? <ErrorAlert error={byCountry.error} /> : null}

			<Card>
				<CardHeader>
					<CardTitle>Top paises por sesiones</CardTitle>
				</CardHeader>
				<CardContent>
					<GeoCountryChart
						data={byCountry.data}
						isLoading={byCountry.isLoading}
					/>
				</CardContent>
			</Card>

			<Card>
				<CardHeader>
					<CardTitle>Paises</CardTitle>
				</CardHeader>
				<CardContent>
					{byCountry.error ? (
						<ErrorAlert error={byCountry.error} />
					) : (
						<GeoCountryTable items={byCountry.data?.items ?? []} />
					)}
				</CardContent>
			</Card>
		</section>
	);
}
