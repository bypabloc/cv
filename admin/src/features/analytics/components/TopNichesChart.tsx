"use client";

import {
	Bar,
	BarChart,
	CartesianGrid,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import type { TopNichesResponse } from "../types";

/**
 * @component TopNichesChart
 * @description Ranking de niches por visitas (analytics/top-niches) como
 *   BarChart de Recharts. Skeleton mientras carga; mensaje si vacio.
 *
 * @props {TopNichesResponse} [data] - ranking del backend
 * @props {boolean} isLoading - estado de carga
 */
export function TopNichesChart({
	data,
	isLoading,
}: {
	data?: TopNichesResponse;
	isLoading: boolean;
}) {
	if (isLoading || !data) {
		return <Skeleton className="h-64 w-full" />;
	}
	if (data.items.length === 0) {
		return (
			<div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
				Sin datos en el rango seleccionado.
			</div>
		);
	}

	return (
		<ResponsiveContainer width="100%" height={256}>
			<BarChart
				data={data.items}
				margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
			>
				<CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
				<XAxis dataKey="niche" tick={{ fontSize: 12 }} />
				<YAxis tick={{ fontSize: 12 }} allowDecimals={false} width={40} />
				<Tooltip
					contentStyle={{
						background: "var(--color-popover)",
						border: "1px solid var(--color-border)",
						borderRadius: 8,
						fontSize: 12,
					}}
				/>
				<Bar
					dataKey="visits"
					fill="var(--color-primary)"
					radius={[4, 4, 0, 0]}
				/>
			</BarChart>
		</ResponsiveContainer>
	);
}
