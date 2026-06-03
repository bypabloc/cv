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

/**
 * @component DistributionChart
 * @description BarChart generico de una distribucion de sesiones (devices
 *   breakdown): normaliza la fila `{<nameKey>: string, sessions: number}` a
 *   `{label, sessions}` y la ordena desc por sessions. Skeleton mientras carga;
 *   mensaje si vacio.
 *
 * @props {Array<Record<string, string | number>>} [data] - filas crudas
 * @props {string} nameKey - clave de la primera columna (device_type/browser/os)
 * @props {boolean} isLoading - estado de carga
 */
export function DistributionChart<T extends { sessions: number }>({
	data,
	nameKey,
	isLoading,
}: {
	data?: T[];
	nameKey: keyof T;
	isLoading: boolean;
}) {
	if (isLoading || !data) {
		return <Skeleton className="h-64 w-full" />;
	}
	if (data.length === 0) {
		return (
			<div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
				Sin datos en el rango seleccionado.
			</div>
		);
	}

	const chartData = [...data]
		.sort((a, b) => b.sessions - a.sessions)
		.map((row) => ({
			label: String(row[nameKey] ?? "-"),
			sessions: row.sessions,
		}));

	return (
		<ResponsiveContainer width="100%" height={256}>
			<BarChart
				data={chartData}
				margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
			>
				<CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
				<XAxis dataKey="label" tick={{ fontSize: 12 }} />
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
