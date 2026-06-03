"use client";

import {
	CartesianGrid,
	Line,
	LineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import type { TimeseriesResponse } from "../types";

/**
 * @component TimeseriesChart
 * @description Serie temporal de eventos (analytics/timeseries) como LineChart
 *   de Recharts. Colores via CSS vars del DS (`--primary`). Skeleton mientras
 *   carga; mensaje si no hay puntos.
 *
 * @props {TimeseriesResponse} [data] - serie del backend
 * @props {boolean} isLoading - estado de carga
 */
export function TimeseriesChart({
	data,
	isLoading,
}: {
	data?: TimeseriesResponse;
	isLoading: boolean;
}) {
	if (isLoading || !data) {
		return <Skeleton className="h-72 w-full" />;
	}
	if (data.points.length === 0) {
		return (
			<div className="flex h-72 items-center justify-center text-sm text-muted-foreground">
				Sin datos en el rango seleccionado.
			</div>
		);
	}

	const chartData = data.points.map((p) => ({
		ts: p.timestamp.slice(0, 10),
		count: p.count,
	}));

	return (
		<ResponsiveContainer width="100%" height={288}>
			<LineChart
				data={chartData}
				margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
			>
				<CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
				<XAxis
					dataKey="ts"
					tick={{ fontSize: 12 }}
					className="text-muted-foreground"
				/>
				<YAxis tick={{ fontSize: 12 }} allowDecimals={false} width={40} />
				<Tooltip
					contentStyle={{
						background: "var(--popover)",
						border: "1px solid var(--border)",
						borderRadius: 8,
						fontSize: 12,
					}}
				/>
				<Line
					type="monotone"
					dataKey="count"
					stroke="var(--primary)"
					strokeWidth={2}
					dot={false}
				/>
			</LineChart>
		</ResponsiveContainer>
	);
}
