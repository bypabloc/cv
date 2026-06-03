"use client";

import { MonitorSmartphone } from "lucide-react";
import { ErrorAlert } from "@/components/ui/error-alert";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { DeviceBreakdown } from "@/features/devices/components/DeviceBreakdown";
import { useBreakdown } from "@/features/devices/hooks/use-breakdown";

/**
 * @page MetricsDevicesPage
 * @description Vista de metricas de dispositivos (`/metrics/devices`):
 *   distribucion de sesiones por tipo de dispositivo, navegador y sistema
 *   operativo (devices/breakdown). El rango from/to es compartido por la page.
 */
export default function MetricsDevicesPage() {
	const { range, setRange } = useMetricsRange();
	const breakdown = useBreakdown(range);

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<MonitorSmartphone className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Dispositivos</h1>
				</div>
				<MetricsDateRange range={range} onChange={setRange} />
			</header>

			{breakdown.error ? <ErrorAlert error={breakdown.error} /> : null}

			<DeviceBreakdown data={breakdown.data} isLoading={breakdown.isLoading} />
		</section>
	);
}
