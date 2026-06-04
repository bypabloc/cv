"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import type { RetentionResponse } from "../types";

/**
 * @component RetentionChart
 * @description New vs returning visitors (analytics/retention) como PieChart de
 *   Recharts + tasa de retorno. Skeleton mientras carga.
 *
 * @props {RetentionResponse} [data] - retencion del backend
 * @props {boolean} isLoading - estado de carga
 */
export function RetentionChart({
	data,
	isLoading,
}: {
	data?: RetentionResponse;
	isLoading: boolean;
}) {
	if (isLoading || !data) {
		return <Skeleton className="h-64 w-full" />;
	}

	const slices = [
		{ name: "Nuevos", value: data.new_visitors, fill: "var(--color-primary)" },
		{
			name: "Recurrentes",
			value: data.returning_visitors,
			fill: "var(--color-muted-foreground)",
		},
	];

	return (
		<div className="flex flex-col items-center gap-3">
			<ResponsiveContainer width="100%" height={224}>
				<PieChart>
					<Pie
						data={slices}
						dataKey="value"
						nameKey="name"
						innerRadius={50}
						outerRadius={80}
						paddingAngle={2}
					>
						{slices.map((slice) => (
							<Cell key={slice.name} fill={slice.fill} />
						))}
					</Pie>
					<Tooltip
						contentStyle={{
							background: "var(--color-popover)",
							border: "1px solid var(--color-border)",
							borderRadius: 8,
							fontSize: 12,
						}}
					/>
				</PieChart>
			</ResponsiveContainer>
			<p className="text-sm text-muted-foreground">
				Tasa de retorno:{" "}
				<span className="font-semibold text-foreground">
					{(data.returning_rate * 100).toFixed(1)}%
				</span>
			</p>
			<p className="max-w-prose text-center text-xs text-muted-foreground">
				<span className="font-medium">Nuevos</span>: primera visita dentro del
				rango. <span className="font-medium">Recurrentes</span>: ya habian
				visitado antes del rango y volvieron. 0% significa que ningun visitante
				previo regreso en este periodo.
			</p>
		</div>
	);
}
