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
import type { GeoByCountryResponse } from "../types";

/**
 * @component GeoCountryChart
 * @description Top 10 paises por sesiones (geo/by-country) como BarChart de
 *   Recharts. Skeleton mientras carga; mensaje si vacio.
 *
 * @props {GeoByCountryResponse} [data] - ranking del backend
 * @props {boolean} isLoading - estado de carga
 */
export function GeoCountryChart({
	data,
	isLoading,
}: {
	data?: GeoByCountryResponse;
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

	const top = [...data.items]
		.sort((a, b) => b.sessions - a.sessions)
		.slice(0, 10);

	return (
		<ResponsiveContainer width="100%" height={256}>
			<BarChart data={top} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
				<CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
				<XAxis dataKey="country" tick={{ fontSize: 12 }} />
				<YAxis tick={{ fontSize: 12 }} allowDecimals={false} width={40} />
				<Tooltip
					contentStyle={{
						background: "var(--popover)",
						border: "1px solid var(--border)",
						borderRadius: 8,
						fontSize: 12,
					}}
				/>
				<Bar dataKey="sessions" fill="var(--primary)" radius={[4, 4, 0, 0]} />
			</BarChart>
		</ResponsiveContainer>
	);
}
